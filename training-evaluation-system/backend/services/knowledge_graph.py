# -*- coding: utf-8 -*-
"""
知识图谱引擎
=============
功能：
  1. 从 JSONL 规范文件中抽取知识点及其关系
  2. 用 LLM 辅助建立知识点之间的关联
  3. 提供查询接口（某知识点的前置知识、相关知识点等）
  4. 对比学生作业，识别薄弱知识点

知识点关系类型：
  - depends_on:        A 依赖 B（学 A 前需要先懂 B）
  - belongs_to:        A 属于 B 的范畴
  - related_to:        A 与 B 相关
  - is_prerequisite:   A 是 B 的前置知识
  - is_part_of:        A 是 B 的一部分
"""

import json
import os
import re
import pickle
from collections import defaultdict

from config import BASE_DIR

# 规范文件目录
SPEC_DIR = os.path.join(BASE_DIR, '..', '..', '开发规范')
# 知识图谱缓存
KG_CACHE_DIR = os.path.join(BASE_DIR, 'rag_cache')
os.makedirs(KG_CACHE_DIR, exist_ok=True)

# 知识点 - 规范来源映射（哪个规范文件包含哪些知识点）
SPEC_FILES = [
    'Ant Design UI.jsonl',
    'Google java规范.jsonl',
    'google C++规范.jsonl',
    '华为C语言规范.jsonl',
    '尼尔森十大原则规范.jsonl',
    '阿里巴巴.Java规范jsonl',
]


class KnowledgeGraph:
    """知识图谱引擎"""

    def __init__(self, llm_service=None):
        self.llm_service = llm_service
        # 图谱数据结构
        self.nodes = {}         # {node_id: {name, category, description, aliases, spec_source}}
        self.edges = []         # [{source, target, relation_type, weight}]
        self.adjacency = defaultdict(list)  # {node_id: [(relation, target_id), ...]}
        self.is_initialized = False
        self._load_or_build()

    # ============================================================
    # 1. 从 JSONL 抽取知识点
    # ============================================================
    def _extract_knowledge_points(self):
        """
        解析 JSONL 文件，初步提取知识点。
        每条记录往往包含多个知识点，我们用规则 + LLM 辅助提取。
        返回: [{"name":"...", "category":"...", "source":"...", "description":"...", "tags":[...]}, ...]
        """
        all_points = []

        for fname in SPEC_FILES:
            filepath = os.path.join(SPEC_DIR, fname)
            if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
                continue

            category = fname.replace('.jsonl', '')
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        item = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    content = item.get('text') or item.get('content') or ''
                    if not content:
                        continue

                    # 从 metadata.tags 中提取知识点标签
                    tags = []
                    meta = item.get('metadata', {})
                    if isinstance(meta, dict) and 'tags' in meta:
                        tags = meta['tags'] if isinstance(meta['tags'], list) else []

                    # 从标题中提取核心知识点
                    title = item.get('title') or item.get('section') or ''
                    core_point = title.split('/')[-1].strip() if title else ''

                    # 每条记录本身作为一个知识点
                    point = {
                        'name': core_point or content[:30],
                        'category': category,
                        'source': fname,
                        'description': content[:200],  # 截取前 200 字作为描述
                        'tags': tags,
                        'full_content': content,
                    }
                    all_points.append(point)

                    # 从 tags 中提取更多知识点
                    for tag in tags:
                        if tag and tag not in [p['name'] for p in all_points]:
                            all_points.append({
                                'name': tag,
                                'category': category,
                                'source': fname,
                                'description': f'标签: {tag}（来自 {core_point}）',
                                'tags': [],
                                'full_content': content[:200],
                            })

        return all_points

    # ============================================================
    # 2. 用 LLM 提取知识点间关系
    # ============================================================
    def _build_relations_via_llm(self, points):
        """
        调用 LLM 分析知识点之间的关系。
        如果 LLM 不可用，使用基于规则的降级方案。
        """
        if not points:
            return [], {}

        # 先构建初始节点
        nodes = {}
        for i, p in enumerate(points):
            node_id = f"kp_{i}"
            nodes[node_id] = {
                'id': node_id,
                'name': p['name'],
                'category': p['category'],
                'source': p['source'],
                'description': p.get('description', ''),
                'tags': p.get('tags', []),
                'full_content': p.get('full_content', ''),
            }

        edges = []

        # 尝试用 LLM 抽取关系
        if self.llm_service:
            try:
                # 按分类分批处理，避免超出 token 限制
                for cat in set(p['category'] for p in points):
                    cat_points = [p for p in points if p['category'] == cat]
                    if len(cat_points) < 2:
                        continue

                    # 构建知识点列表
                    points_text = "\n".join([
                        f"{i+1}. {p['name']} — {p.get('description', '')[:100]}"
                        for i, p in enumerate(cat_points[:20])  # 每批最多 20 个
                    ])

                    prompt = f"""你是一个知识图谱构建专家。请分析以下知识点之间的语义关系，输出 JSON 格式。

知识点列表：
{points_text}

请识别它们之间的关系，可能的类型：
- depends_on: A 依赖 B（学 A 前需要先懂 B）
- belongs_to: A 属于 B
- related_to: A 与 B 相关
- is_part_of: A 是 B 的一部分

请按以下格式返回（最多 30 条关系）：
{{"relations": [
    {{"source": "知识点名称", "target": "知识点名称", "type": "depends_on"}},
    ...
]}}
"""
                    messages = [{'role': 'user', 'content': prompt}]
                    response = self.llm_service.chat_completion(
                        messages, temperature=0.2, max_tokens=2000
                    )

                    # 解析 LLM 返回的 JSON
                    try:
                        start = response.find('{')
                        end = response.rfind('}') + 1
                        if start != -1 and end > start:
                            result = json.loads(response[start:end])
                            for rel in result.get('relations', []):
                                src_name = rel.get('source', '')
                                tgt_name = rel.get('target', '')
                                rel_type = rel.get('type', 'related_to')
                                # 查找对应的 node_id
                                src_id = self._find_node_id(nodes, src_name)
                                tgt_id = self._find_node_id(nodes, tgt_name)
                                if src_id and tgt_id and src_id != tgt_id:
                                    edges.append({
                                        'source': src_id,
                                        'target': tgt_id,
                                        'relation_type': rel_type,
                                        'weight': 1.0,
                                    })
                    except (json.JSONDecodeError, ValueError):
                        pass
            except Exception as e:
                print(f"[知识图谱] LLM 关系抽取失败: {e}，使用规则降级")

        # 降级方案：基于标签和名称的规则匹配
        if not edges:
            edges = self._rule_based_relations(nodes)

        return nodes, edges

    def _find_node_id(self, nodes, name):
        """根据知识点名称查找 node_id（模糊匹配）"""
        name = name.strip().lower()
        for nid, node in nodes.items():
            if node['name'].lower() == name:
                return nid
        # 包含匹配
        for nid, node in nodes.items():
            if name in node['name'].lower() or node['name'].lower() in name:
                return nid
        return None

    def _rule_based_relations(self, nodes):
        """基于规则的降级关系抽取"""
        edges = []
        node_list = list(nodes.items())

        for i, (nid_a, node_a) in enumerate(node_list):
            # 同分类下，名称包含关系 → is_part_of
            for j, (nid_b, node_b) in enumerate(node_list):
                if i == j or node_a['category'] != node_b['category']:
                    continue
                # A 的名称包含 B → B is_part_of A
                if node_a['name'] and node_b['name'] and \
                   len(node_a['name']) > len(node_b['name']) and \
                   node_b['name'] in node_a['name']:
                    edges.append({
                        'source': nid_b, 'target': nid_a,
                        'relation_type': 'is_part_of', 'weight': 0.8,
                    })
                # 共享 tags → related_to
                common_tags = set(node_a.get('tags', [])) & set(node_b.get('tags', []))
                if common_tags:
                    edges.append({
                        'source': nid_a, 'target': nid_b,
                        'relation_type': 'related_to', 'weight': 0.5,
                    })

        return edges

    # ============================================================
    # 3. 构建与缓存
    # ============================================================
    def _load_or_build(self):
        cache_path = os.path.join(KG_CACHE_DIR, 'knowledge_graph.pkl')
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    data = pickle.load(f)
                    self.nodes = data['nodes']
                    self.edges = data['edges']
                    self._build_adjacency()
                    self.is_initialized = True
                    print(f"[知识图谱] 从缓存加载: {len(self.nodes)} 节点, {len(self.edges)} 边")
                    return
            except Exception as e:
                print(f"[知识图谱] 缓存加载失败: {e}")

        # 重新构建
        points = self._extract_knowledge_points()
        nodes, edges = self._build_relations_via_llm(points)
        self.nodes = nodes
        self.edges = edges
        self._build_adjacency()
        self.is_initialized = True

        # 保存缓存
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump({'nodes': nodes, 'edges': edges}, f)
            print(f"[知识图谱] 已构建并缓存: {len(nodes)} 节点, {len(edges)} 边")
        except Exception as e:
            print(f"[知识图谱] 缓存保存失败: {e}")

    def _build_adjacency(self):
        self.adjacency = defaultdict(list)
        for edge in self.edges:
            self.adjacency[edge['source']].append((edge['relation_type'], edge['target']))
            self.adjacency[edge['target']].append((f"reverse_{edge['relation_type']}", edge['source']))

    # ============================================================
    # 4. 核心查询接口
    # ============================================================
    def get_prerequisites(self, knowledge_name):
        """获取某个知识点的前置知识"""
        node_id = self._find_node_id(self.nodes, knowledge_name)
        if not node_id:
            return []

        prereqs = []
        visited = set()
        def dfs(nid, depth=0):
            if nid in visited or depth > 3:
                return
            visited.add(nid)
            for rel_type, target_id in self.adjacency.get(nid, []):
                # depends_on 和 reverse_is_part_of 表示依赖关系
                if rel_type in ('depends_on', 'reverse_is_part_of'):
                    prereqs.append({
                        'name': self.nodes[target_id]['name'],
                        'relation': rel_type,
                        'category': self.nodes[target_id]['category'],
                    })
                    dfs(target_id, depth + 1)

        dfs(node_id)
        return prereqs

    def get_related_knowledge(self, knowledge_name):
        """获取相关知识"""
        node_id = self._find_node_id(self.nodes, knowledge_name)
        if not node_id:
            return []

        related = []
        for rel_type, target_id in self.adjacency.get(node_id, []):
            related.append({
                'name': self.nodes[target_id]['name'],
                'relation': rel_type,
                'category': self.nodes[target_id]['category'],
            })
        return related

    def get_all_knowledge_points(self):
        """获取所有知识点"""
        return [
            {'id': nid, 'name': node['name'], 'category': node['category']}
            for nid, node in self.nodes.items()
        ]

    # ============================================================
    # 5. 学生薄弱点分析（核心）
    # ============================================================
    def analyze_weak_points(self, homework_content, all_knowledge_points=None):
        """
        分析学生作业，找出薄弱知识点。

        Args:
            homework_content: 学生提交的作业内容
            all_knowledge_points: 可选，限制分析范围的知识点列表

        Returns:
            [{"name":"知识点名", "mastery":0.3, "reason":"分析理由", "suggested_courses":[]}, ...]
        """
        if not homework_content:
            return []

        # 获取所有知识点名称
        kp_list = all_knowledge_points or list(self.nodes.values())
        kp_names = [kp['name'] for kp in kp_list if kp.get('name')]

        if not kp_names:
            return []

        # 用 LLM 分析
        if self.llm_service:
            kp_text = "\n".join([f"- {name}" for name in kp_names[:30]])  # 限制数量

            prompt = f"""你是一名教育评估专家。请分析学生的作业内容，判断以下知识点的掌握程度。

【知识点列表】
{kp_text}

【学生作业内容】
{homework_content[:4000]}

请分析学生对每个知识点的掌握程度（0.0~1.0），并给出理由。
按以下 JSON 格式返回（只返回掌握程度 < 0.7 的薄弱知识点）：

{{"weak_points": [
    {{"knowledge_point": "知识点名称", "mastery": 0.3, "reason": "学生在xxx方面表现不足"}},
    ...
]}}
"""
            messages = [{'role': 'user', 'content': prompt}]
            try:
                response = self.llm_service.chat_completion(
                    messages, temperature=0.3, max_tokens=2000
                )
                start = response.find('{')
                end = response.rfind('}') + 1
                if start != -1 and end > start:
                    result = json.loads(response[start:end])
                    weak_points = result.get('weak_points', [])
                    # 补充前置知识
                    for wp in weak_points:
                        prereqs = self.get_prerequisites(wp['knowledge_point'])
                        wp['prerequisites'] = [p['name'] for p in prereqs]
                    return weak_points
            except Exception as e:
                print(f"[知识图谱] 薄弱点分析失败: {e}")

        # 降级：简单关键词匹配
        weak_points = []
        homework_lower = homework_content.lower()
        for kp in kp_list[:20]:
            name = kp.get('name', '')
            if not name:
                continue
            # 如果作业中很少提到该知识点，标记为薄弱
            count = homework_lower.count(name.lower())
            mastery = min(1.0, count / 3)  # 提到3次以上算掌握
            if mastery < 0.5:
                weak_points.append({
                    'knowledge_point': name,
                    'mastery': round(mastery, 2),
                    'reason': '作业中对该知识点涉及较少' if count == 0 else '作业中对该知识点涉及不充分',
                    'prerequisites': [],
                })
        return weak_points[:10]

    # ============================================================
    # 6. 统计信息
    # ============================================================
    def get_stats(self):
        return {
            'total_nodes': len(self.nodes),
            'total_edges': len(self.edges),
            'categories': list(set(n['category'] for n in self.nodes.values())),
        }


# 全局单例
_kg_instance = None

def get_knowledge_graph(llm_service=None):
    global _kg_instance
    if _kg_instance is None:
        _kg_instance = KnowledgeGraph(llm_service)
    return _kg_instance
