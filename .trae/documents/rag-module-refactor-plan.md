# RAG 模块独立化 + 按需构建 改造计划

## 背景与目标

当前 RAG（基于开发规范的检索增强生成）功能存在两个问题：
1. **启动即构建/加载索引**：[`main.py`](file:///f:/xiangmu/training-evaluation-system/backend/main.py#L23-L29) 启动时调用 `llm_service.init_rag()`，若缓存不存在或规范文件更新，会立即调用 Embedding 接口，消耗 token。
2. **代码未独立**：RAG 逻辑全部堆在 [`services/rag_service.py`](file:///f:/xiangmu/training-evaluation-system/backend/services/rag_service.py)，缓存目录 [`backend/rag_cache/`](file:///f:/xiangmu/training-evaluation-system/backend/rag_cache) 也没有单独管理。

用户选择保留 RAG，但要求：
- 把 RAG 拆成独立模块/文件夹
- 向量索引只在**手动触发重建**时构建一次，启动时不自动调用 Embedding

## 关键现状

- 已存在手动重建接口：`POST /api/modify/rebuild-index`（见 [`routers/modify.py`](file:///f:/xiangmu/training-evaluation-system/backend/routers/modify.py#L127-L142)）
- 已存在缓存机制：索引保存到 `backend/rag_cache/rag_index.pkl`（见 [`rag_service.py`](file:///f:/xiangmu/training-evaluation-system/backend/services/rag_service.py#L189-L219)）
- 前端已封装 `modifyAPI.rebuildIndex()`（见 [`frontend/src/api/index.js`](file:///f:/xiangmu/training-evaluation-system/frontend/src/api/index.js#L106)）
- 调用 RAG 的地方：
  - [`routers/modify.py`](file:///f:/xiangmu/training-evaluation-system/backend/routers/modify.py)：作业修改、规范列表、分类列表、重建索引
  - [`services/llm_service.py`](file:///f:/xiangmu/training-evaluation-system/backend/services/llm_service.py#L385-L389)：`init_rag()` 注入 LLM 实例

## 改造方案

### 1. 新建 `backend/rag/` 独立包

目录结构：
```
backend/
  rag/
    __init__.py          # 对外导出 RAGEngine、get_rag_engine、get_spec_files_info 等
    engine.py            # 从原 rag_service.py 迁移 RAGEngine 类
    config.py            # RAG 专属配置：SPEC_DIR、RAG_CACHE_DIR、TOP_K 等
    cache/               # 向量索引缓存目录（原 backend/rag_cache/ 迁移至此）
```

### 2. 调整 RAGEngine 初始化逻辑

- 构造函数不再自动调用 `_load_or_build_index()`
- 新增 `load_cache()`：仅读取已有缓存，**不调用 Embedding 接口**
- 保留 `rebuild_index()`：强制读取规范文件、生成 embedding、保存缓存
- `retrieve()` 在未加载索引时直接返回空结果

这样：
- 启动时不触发任何 Embedding 调用
- 只有在教师/管理员点击「重建索引」时才会消费 token

### 3. 移除启动时自动初始化

在 [`main.py`](file:///f:/xiangmu/training-evaluation-system/backend/main.py#L23-L29) 中删除或注释掉：
```python
llm_service.init_rag()
```

### 4. 更新引用路径

需要修改的文件：
- [`backend/services/llm_service.py`](file:///f:/xiangmu/training-evaluation-system/backend/services/llm_service.py)：
  - 修改 `init_rag()` / `modify_submission()` 中的 `from services.rag_service import ...` 为 `from rag import ...`
  - `init_rag()` 改为只获取引擎实例、注入 `llm_service`，不主动构建
- [`backend/routers/modify.py`](file:///f:/xiangmu/training-evaluation-system/backend/routers/modify.py)：
  - 修改 `from services.rag_service import ...` 为 `from rag import ...`
  - `handle_modify_submission` 中去掉显式 `llm_service.init_rag()` 调用，改为获取引擎
- （可选）保留 [`backend/services/rag_service.py`](file:///f:/xiangmu/training-evaluation-system/backend/services/rag_service.py) 作为兼容性转发文件，避免遗漏的 import 报错

### 5. 缓存目录迁移

- 将现有 `backend/rag_cache/` 下的 `rag_index.pkl` 移动到 `backend/rag/cache/rag_index.pkl`
- 更新 [`rag/config.py`](file:///f:/xiangmu/training-evaluation-system/backend/rag/config.py) 中的 `RAG_CACHE_DIR`

### 6. 前端无需改动

前端已经通过 `modifyAPI.rebuildIndex()` 调用重建接口，本次后端改造对它透明。

## 需要用户确认的点

1. **Embedding 提供方**：当前 `get_embedding` 只兼容 OpenAI / Ollama，不兼容讯飞。重建索引前需要：
   - 配置 OpenAI API Key，或
   - 本地安装 Ollama + embedding 模型（免费），或
   - 后续再为讯飞实现 embedding 接口（可作为二期）
2. **规范文件目录**：当前规范文件在 `backend/../开发规范/`，是否保持不动？建议保持不动，RAG 模块只读取该目录。
3. **旧缓存**：是否保留现有 `rag_index.pkl`？建议保留并迁移到新目录，避免首次启动后索引为空。

## 验证步骤

1. 启动后端，确认日志中不再出现 `[LLM] OpenAI embedding 失败` 或 `[RAG] 正在构建向量索引`
2. 调用 `GET /api/modify/specs`，确认返回规范文件列表，但 `index_stats.total` 为 0（未构建/未加载缓存时）
3. 调用 `POST /api/modify/rebuild-index`，确认返回索引条数，且只产生一次 Embedding token 消耗
4. 再次调用 `GET /api/modify/specs`，确认 `index_stats.total` 为实际索引数
5. 重启后端，确认不触发重建，且 `GET /api/modify/specs` 能正确加载缓存
6. 调用 `POST /api/modify/submission` 测试作业修改功能是否正常

## 影响范围

- 后端文件：新增 `backend/rag/` 包；修改 `main.py`、`services/llm_service.py`、`routers/modify.py`
- 前端：无改动
- 数据库：无改动
- 向量缓存：从 `backend/rag_cache/` 迁移到 `backend/rag/cache/`
