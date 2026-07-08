# -*- coding: utf-8 -*-
"""
作业修改模块（基于开发规范 + RAG + LLM）
===========================================
API:
  POST /api/modify/submission    — 修改单个作业
  GET  /api/modify/specs         — 获取规范文件列表
  GET  /api/modify/categories    — 获取规范分类列表
  POST /api/modify/rebuild-index — 重建 RAG 索引

依赖:
  - rag                   (RAG 检索引擎，位于 backend/rag/)
  - services.llm_service  (LLM 修改方法)
  - routers.auth          (权限控制)
"""

import json
import os

from services.llm_service import llm_service
from rag import get_rag_engine, get_spec_files_info
from routers import auth


# ============================================================
# 修改单个作业
# POST /api/modify/submission
# ============================================================
def handle_modify_submission(handler):
    """基于开发规范修改学生作业"""
    user, err = auth.require_teacher_or_admin(handler)
    if err:
        return err

    data = handler.parse_json_body()

    # 必填参数
    content = data.get('content', '').strip()
    if not content:
        return 400, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '缺少必填参数 content（作业内容）'}, ensure_ascii=False
        )

    # 可选参数
    modification_type = data.get('modification_type', 'code')  # code / ui / all / custom
    custom_requirements = data.get('custom_requirements', '')
    category_filter = data.get('category_filter', None)  # 如 'Ant Design UI'

    try:
        # 获取 RAG 引擎（只加载已有缓存，不会自动构建索引）
        get_rag_engine(llm_service)

        # 调用核心方法
        result = llm_service.modify_submission(
            content=content,
            modification_type=modification_type,
            custom_requirements=custom_requirements,
            category_filter=category_filter
        )

        return 200, [('Content-Type', 'application/json')], json.dumps(
            result, ensure_ascii=False
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return 500, [('Content-Type', 'application/json')], json.dumps(
            {'detail': f'修改作业失败: {str(e)}'}, ensure_ascii=False
        )


# ============================================================
# 获取规范文件列表
# GET /api/modify/specs
# ============================================================
def handle_get_specs(handler):
    """获取开发规范 JSONL 文件列表及状态"""
    user, err = auth.require_user(handler)
    if err:
        return err

    files_info = get_spec_files_info()

    # 获取 RAG 引擎统计
    try:
        rag = get_rag_engine(llm_service)
        stats = rag.get_stats()
    except Exception:
        stats = {"total": 0, "categories": {}}

    return 200, [('Content-Type', 'application/json')], json.dumps({
        'files': files_info,
        'index_stats': stats,
    }, ensure_ascii=False)


# ============================================================
# 获取规范分类列表
# GET /api/modify/categories
# ============================================================
def handle_get_categories(handler):
    """获取所有可用的规范分类"""
    user, err = auth.require_user(handler)
    if err:
        return err

    try:
        rag = get_rag_engine(llm_service)
        categories = rag.get_available_categories()
        stats = rag.get_stats()
    except Exception as e:
        return 500, [('Content-Type', 'application/json')], json.dumps(
            {'detail': str(e)}, ensure_ascii=False
        )

    return 200, [('Content-Type', 'application/json')], json.dumps({
        'categories': categories,
        'stats': stats,
    }, ensure_ascii=False)


# ============================================================
# 重建 RAG 索引
# POST /api/modify/rebuild-index
# ============================================================
def handle_rebuild_index(handler):
    """强制重建 RAG 向量索引"""
    user, err = auth.require_teacher_or_admin(handler)
    if err:
        return err

    try:
        rag = get_rag_engine(llm_service)
        count = rag.rebuild_index()
        return 200, [('Content-Type', 'application/json')], json.dumps({
            'message': f'索引重建完成，共索引 {count} 条规范',
            'total': count,
        }, ensure_ascii=False)
    except Exception as e:
        return 500, [('Content-Type', 'application/json')], json.dumps(
            {'detail': f'索引重建失败: {str(e)}'}, ensure_ascii=False
        )
