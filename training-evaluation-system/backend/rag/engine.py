# -*- coding: utf-8 -*-
"""
RAG 检索引擎
==============
功能：
  1. 加载开发规范 JSONL 文件，分块解析
  2. 使用 LLM 的 embedding 接口（或 Ollama embedding）进行向量化
  3. 基于余弦相似度检索最相关的规范条目
  4. 将检索结果组装为 LLM 上下文

架构选择：
  - 不使用第三方向量数据库（如 Chroma/Pinecone）
  - 使用内存 + 文件缓存的轻量方案
  - 向量化复用已有的 LLM 连接（OpenAI 兼容接口 / Ollama）
  - 启动时只加载已有缓存，不自动构建索引；构建需显式调用 rebuild_index()
"""

import json
import os
import pickle

import numpy as np

from config import BASE_DIR
from rag.config import SPEC_DIR, RAG_CACHE_DIR, TOP_K, SIMILARITY_THRESHOLD, SPEC_FILES


class RAGEngine:
    """RAG 检索与上下文组装引擎"""

    def __init__(self, llm_service=None):
        """
        Args:
            llm_service: LLMService 实例，用于调用 embedding 接口
                         如果为 None，则使用内置的 TF-IDF 关键词匹配（降级方案）
        """
        self.llm_service = llm_service
        self.documents = []      # [{id, title, content, category, source, embedding}]
        self.is_indexed = False
        # 启动时仅尝试加载已有缓存，不自动构建索引
        self._load_cache_silent()

    # ----------------------------------------------------------
    # 1. JSONL 加载与解析
    # ----------------------------------------------------------
    def _load_jsonl_files(self):
        """扫描 SPEC_DIR 目录下的所有 JSONL 文件，解析为文档块"""
        all_docs = []

        for fname in SPEC_FILES:
            filepath = os.path.join(SPEC_DIR, fname)
            if not os.path.exists(filepath):
                print(f"[RAG] 规范文件不存在，跳过: {fname}")
                continue

            # 读取文件大小，空文件跳过
            if os.path.getsize(filepath) == 0:
                print(f"[RAG] 规范文件为空，跳过: {fname}")
                continue

            category = fname.replace('.jsonl', '')
            with open(filepath, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        item = json.loads(line)
                    except json.JSONDecodeError:
                        print(f"[RAG] JSON 解析失败 {fname}:{line_num}，跳过")
                        continue

                    # 提取文本内容（兼容不同 JSONL 格式）
                    doc_id = f"{category}_{item.get('id', line_num)}"
                    title = item.get('title') or item.get('section') or item.get('metadata', {}).get('title', '')
                    content = item.get('text') or item.get('content') or ''

                    # 跳过空内容
                    if not content.strip():
                        continue

                    all_docs.append({
                        'id': doc_id,
                        'title': title,
                        'content': content,
                        'category': category,
                        'source': fname,
                        'metadata': item.get('metadata', {}),
                    })

        print(f"[RAG] 共加载 {len(all_docs)} 条规范条目")
        return all_docs

    # ----------------------------------------------------------
    # 2. Embedding 生成
    # ----------------------------------------------------------
    def _get_embedding(self, text):
        """
        生成文本的向量嵌入。
        策略：
          1. 如果有 llm_service，尝试调用 OpenAI 兼容的 embedding 接口
          2. 否则退化为基于字符统计的简单向量（仅用于演示/降级）
        """
        if not text or not text.strip():
            return None

        if self.llm_service:
            try:
                # 方法一：调用 OpenAI 兼容的 embedding API
                embedding = self.llm_service.get_embedding(text)
                if embedding is not None:
                    return np.array(embedding, dtype=np.float32)
            except Exception as e:
                print(f"[RAG] Embedding API 调用失败: {e}，使用降级方案")

        # 方法二（降级）：使用简单的 TF-IDF 风格统计向量
        return self._fallback_embedding(text)

    def _fallback_embedding(self, text):
        """降级方案：基于字符 n-gram 频率的向量"""
        # 使用字符二元组和三元组构造特征向量（256维）
        np.random.seed(42)
        dim = 256
        vec = np.zeros(dim, dtype=np.float32)

        # 提取字符 n-gram
        text_lower = text.lower()
        for i in range(len(text_lower) - 1):
            idx = hash(text_lower[i:i+2]) % dim
            vec[idx] += 1
        for i in range(len(text_lower) - 2):
            idx = hash(text_lower[i:i+3]) % dim
            vec[idx] += 0.5

        # L2 归一化
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec

    # ----------------------------------------------------------
    # 3. 索引构建与缓存
    # ----------------------------------------------------------
    def _build_index(self, documents):
        """对所有文档计算 embedding，构建索引"""
        print(f"[RAG] 正在构建向量索引（共 {len(documents)} 条）...")
        indexed = []
        for i, doc in enumerate(documents):
            embedding = self._get_embedding(doc['content'])
            if embedding is not None:
                doc['embedding'] = embedding
                indexed.append(doc)
            if (i + 1) % 50 == 0:
                print(f"[RAG] 已处理 {i+1}/{len(documents)} 条")
        print(f"[RAG] 索引构建完成，成功索引 {len(indexed)}/{len(documents)} 条")
        return indexed

    def _save_cache(self, documents):
        """将向量索引保存到磁盘缓存"""
        cache_path = os.path.join(RAG_CACHE_DIR, 'rag_index.pkl')
        # 移除 embedding 的 numpy 引用以便序列化
        save_data = []
        for doc in documents:
            d = dict(doc)
            if 'embedding' in d and d['embedding'] is not None:
                d['embedding'] = d['embedding'].tolist()
            save_data.append(d)
        with open(cache_path, 'wb') as f:
            pickle.dump(save_data, f)
        print(f"[RAG] 索引缓存已保存: {cache_path}")

    def _load_cache(self):
        """从磁盘缓存加载向量索引，返回数据或 None"""
        cache_path = os.path.join(RAG_CACHE_DIR, 'rag_index.pkl')
        if not os.path.exists(cache_path):
            return None
        try:
            with open(cache_path, 'rb') as f:
                data = pickle.load(f)
            # 恢复 embedding 为 numpy 数组
            for doc in data:
                if 'embedding' in doc and doc['embedding'] is not None:
                    doc['embedding'] = np.array(doc['embedding'], dtype=np.float32)
            print(f"[RAG] 从缓存加载 {len(data)} 条索引")
            return data
        except Exception as e:
            print(f"[RAG] 缓存加载失败: {e}")
            return None

    def _load_cache_silent(self):
        """启动时尝试加载缓存，不触发构建"""
        cached = self._load_cache()
        if cached:
            self.documents = cached
            self.is_indexed = True
        else:
            print("[RAG] 未找到缓存索引，请在需要时手动重建（/api/modify/rebuild-index）")

    # ----------------------------------------------------------
    # 4. 重建索引（供 API 调用）
    # ----------------------------------------------------------
    def rebuild_index(self):
        """强制重建索引"""
        docs = self._load_jsonl_files()
        if docs:
            self.documents = self._build_index(docs)
            self._save_cache(self.documents)
            self.is_indexed = True
            return len(self.documents)
        return 0

    # ----------------------------------------------------------
    # 5. 检索（核心方法）
    # ----------------------------------------------------------
    def retrieve(self, query, top_k=None, category_filter=None):
        """
        根据查询文本检索最相关的规范条目。

        Args:
            query: 查询文本（如学生作业的代码/UI描述）
            top_k: 返回条目数（默认 TOP_K）
            category_filter: 规范分类过滤（如 'Ant Design UI'），None 表示全部

        Returns:
            [{"id","title","content","category","source","similarity"}, ...]
        """
        if top_k is None:
            top_k = TOP_K

        if not self.is_indexed or not self.documents:
            print("[RAG] 索引未就绪，返回空结果")
            return []

        # 生成查询的 embedding
        query_vec = self._get_embedding(query)
        if query_vec is None:
            print("[RAG] 查询向量生成失败")
            return []

        # 计算余弦相似度（利用 numpy 批量计算加速）
        results = []
        for doc in self.documents:
            if doc['embedding'] is None:
                continue

            # 分类过滤
            if category_filter and doc['category'] != category_filter:
                continue

            # 余弦相似度
            sim = float(np.dot(query_vec, doc['embedding']))
            if sim >= SIMILARITY_THRESHOLD:
                results.append({
                    'id': doc['id'],
                    'title': doc['title'],
                    'content': doc['content'],
                    'category': doc['category'],
                    'source': doc['source'],
                    'similarity': round(sim, 4),
                })

        # 按相似度排序，取 Top-K
        results.sort(key=lambda x: x['similarity'], reverse=True)
        results = results[:top_k]

        return results

    # ----------------------------------------------------------
    # 6. 检索结果 → Prompt 上下文
    # ----------------------------------------------------------
    def build_context(self, query, top_k=None, category_filter=None):
        """
        检索相关规范并组装为 LLM 可用的上下文文本。

        Args:
            query: 查询文本
            top_k: 返回条目数

        Returns:
            (context_text, retrieved_docs)
        """
        docs = self.retrieve(query, top_k, category_filter)

        if not docs:
            return "", []

        # 按分类分组，生成结构化上下文
        context_parts = []
        context_parts.append("【相关开发规范参考】\n")

        current_cat = None
        for i, doc in enumerate(docs, 1):
            if doc['category'] != current_cat:
                current_cat = doc['category']
                context_parts.append(f"\n--- {current_cat} ---")

            context_parts.append(
                f"[规范{i}] {doc['title']}\n"
                f"内容：{doc['content']}\n"
            )

        context_text = "\n".join(context_parts)
        return context_text, docs

    # ----------------------------------------------------------
    # 7. 统计信息
    # ----------------------------------------------------------
    def get_stats(self):
        """返回索引统计信息"""
        if not self.documents:
            return {"total": 0, "categories": {}}

        stats = {"total": len(self.documents), "categories": {}}
        for doc in self.documents:
            cat = doc['category']
            if cat not in stats['categories']:
                stats['categories'][cat] = 0
            stats['categories'][cat] += 1
        return stats

    def get_available_categories(self):
        """返回可用的规范分类列表"""
        cats = set()
        for doc in self.documents:
            cats.add(doc['category'])
        return sorted(cats)


# ============================================================
# 全局单例
# ============================================================
_rag_engine = None


def get_rag_engine(llm_service=None):
    """获取 RAG 引擎单例"""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine(llm_service)
    # 允许外部注入/更新 llm_service
    if llm_service is not None:
        _rag_engine.llm_service = llm_service
    return _rag_engine


# ============================================================
# 辅助：获取 JSONL 文件列表（含状态）
# ============================================================
def get_spec_files_info():
    """返回规范文件信息列表"""
    files_info = []
    for fname in SPEC_FILES:
        filepath = os.path.join(SPEC_DIR, fname)
        info = {
            'filename': fname,
            'exists': os.path.exists(filepath),
            'size': os.path.getsize(filepath) if os.path.exists(filepath) else 0,
            'path': filepath,
        }
        files_info.append(info)
    return files_info
