# -*- coding: utf-8 -*-
"""
知识图谱与课程推荐 API
======================
API:
  GET  /api/knowledge/graph         — 获取知识图谱概览
  GET  /api/knowledge/points        — 获取所有知识点
  GET  /api/knowledge/prerequisites — 查询某知识点的前置知识
  POST /api/knowledge/analyze       — 分析学生作业的薄弱知识点
  POST /api/recommend/courses       — 根据薄弱点推荐课程
  POST /api/recommend/analyze-and-recommend — 一站式：分析+推荐
"""

import json

from services.knowledge_graph import get_knowledge_graph
from services.recommendation import get_recommendation_engine
from services.llm_service import llm_service
from routers import auth


# ============================================================
# 获取知识图谱概览
# GET /api/knowledge/graph
# ============================================================
def handle_get_graph(handler):
    """获取知识图谱概览（节点数、分类等统计）"""
    user, err = auth.require_user(handler)
    if err:
        return err

    try:
        kg = get_knowledge_graph(llm_service)
        stats = kg.get_stats()
        return 200, [('Content-Type', 'application/json')], json.dumps({
            'stats': stats,
            'nodes_count': stats['total_nodes'],
            'edges_count': stats['total_edges'],
            'categories': stats['categories'],
        }, ensure_ascii=False)
    except Exception as e:
        return 500, [('Content-Type', 'application/json')], json.dumps(
            {'detail': str(e)}, ensure_ascii=False
        )


# ============================================================
# 获取所有知识点
# GET /api/knowledge/points
# ============================================================
def handle_get_points(handler):
    """获取知识图谱中的所有知识点"""
    user, err = auth.require_user(handler)
    if err:
        return err

    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(handler.path)
    query = parse_qs(parsed.query)
    category = query.get('category', [None])[0]

    try:
        kg = get_knowledge_graph(llm_service)
        points = kg.get_all_knowledge_points()

        if category:
            points = [p for p in points if p['category'] == category]

        return 200, [('Content-Type', 'application/json')], json.dumps({
            'total': len(points),
            'points': points,
        }, ensure_ascii=False)
    except Exception as e:
        return 500, [('Content-Type', 'application/json')], json.dumps(
            {'detail': str(e)}, ensure_ascii=False
        )


# ============================================================
# 查询前置知识
# GET /api/knowledge/prerequisites?name=xxx
# ============================================================
def handle_get_prerequisites(handler):
    """查询知识点的前置知识"""
    user, err = auth.require_user(handler)
    if err:
        return err

    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(handler.path)
    query = parse_qs(parsed.query)
    name = query.get('name', [None])[0]

    if not name:
        return 400, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '缺少参数 name（知识点名称）'}, ensure_ascii=False
        )

    try:
        kg = get_knowledge_graph(llm_service)
        prereqs = kg.get_prerequisites(name)
        related = kg.get_related_knowledge(name)

        return 200, [('Content-Type', 'application/json')], json.dumps({
            'knowledge_point': name,
            'prerequisites': prereqs,
            'related_knowledge': related,
        }, ensure_ascii=False)
    except Exception as e:
        return 500, [('Content-Type', 'application/json')], json.dumps(
            {'detail': str(e)}, ensure_ascii=False
        )


# ============================================================
# 分析作业薄弱点
# POST /api/knowledge/analyze
# ============================================================
def handle_analyze_weakness(handler):
    """分析学生作业内容，找出薄弱知识点"""
    user, err = auth.require_teacher_or_admin(handler)
    if err:
        return err

    data = handler.parse_json_body()
    content = data.get('content', '').strip()
    if not content:
        return 400, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '缺少必填参数 content（作业内容）'}, ensure_ascii=False
        )

    try:
        kg = get_knowledge_graph(llm_service)
        weak_points = kg.analyze_weak_points(content)

        return 200, [('Content-Type', 'application/json')], json.dumps({
            'weak_points': weak_points,
            'total_weakness': len(weak_points),
            'analysis_summary': f'发现 {len(weak_points)} 个薄弱知识点' if weak_points else '未发现明显薄弱点',
        }, ensure_ascii=False)
    except Exception as e:
        return 500, [('Content-Type', 'application/json')], json.dumps(
            {'detail': f'分析失败: {str(e)}'}, ensure_ascii=False
        )


# ============================================================
# 根据薄弱点推荐课程
# POST /api/recommend/courses
# ============================================================
def handle_recommend_courses(handler):
    """根据薄弱知识点推荐课程"""
    user, err = auth.require_user(handler)
    if err:
        return err

    data = handler.parse_json_body()
    weak_points = data.get('weak_points', [])

    if not weak_points:
        return 400, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '缺少必填参数 weak_points（薄弱知识点列表）'}, ensure_ascii=False
        )

    top_k = data.get('top_k', 5)

    try:
        kg = get_knowledge_graph(llm_service)
        rec_engine = get_recommendation_engine(kg, llm_service)
        result = rec_engine.recommend_with_explanation(weak_points, top_k=top_k)

        return 200, [('Content-Type', 'application/json')], json.dumps(
            result, ensure_ascii=False
        )
    except Exception as e:
        return 500, [('Content-Type', 'application/json')], json.dumps(
            {'detail': f'推荐失败: {str(e)}'}, ensure_ascii=False
        )


# ============================================================
# 一站式：分析 + 推荐
# POST /api/recommend/analyze-and-recommend
# ============================================================
def handle_analyze_and_recommend(handler):
    """一站式接口：分析作业薄弱点 → 推荐课程"""
    user, err = auth.require_user(handler)
    if err:
        return err

    data = handler.parse_json_body()
    content = data.get('content', '').strip()
    if not content:
        return 400, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '缺少必填参数 content（作业内容）'}, ensure_ascii=False
        )

    top_k = data.get('top_k', 5)

    try:
        kg = get_knowledge_graph(llm_service)
        rec_engine = get_recommendation_engine(kg, llm_service)

        # 步骤1：分析薄弱点
        weak_points = kg.analyze_weak_points(content)

        # 步骤2：推荐课程
        result = rec_engine.recommend_with_explanation(weak_points, top_k=top_k)

        return 200, [('Content-Type', 'application/json')], json.dumps({
            'weak_points': weak_points,
            'total_weakness': len(weak_points),
            **result,
        }, ensure_ascii=False)
    except Exception as e:
        return 500, [('Content-Type', 'application/json')], json.dumps(
            {'detail': f'分析推荐失败: {str(e)}'}, ensure_ascii=False
        )
