# -*- coding: utf-8 -*-
"""
课程推荐引擎
=============
功能：
  1. 将实训项目/课程与知识点关联
  2. 根据学生薄弱知识点，推荐相关课程
  3. 支持多种推荐策略

推荐流程：
  学生薄弱知识点 → 匹配覆盖该知识点的课程 → 按覆盖率和难度排序 → 返回推荐列表
  
与知识图谱的配合：
  - 如果一个知识点学生掌握不好，优先推荐包含该知识点的课程
  - 同时推荐该知识点前置知识的课程（补基础）
  - 也推荐该知识点相关领域的课程（拓宽知识面）
"""

import json
import os
import re
from collections import defaultdict

from database import get_db, dict_from_row


class RecommendationEngine:
    """课程推荐引擎"""

    def __init__(self, knowledge_graph=None, llm_service=None):
        """
        Args:
            knowledge_graph: KnowledgeGraph 实例，用于知识关系查询
            llm_service: LLMService 实例，用于智能推荐分析
        """
        self.kg = knowledge_graph
        self.llm_service = llm_service
        # 课程-知识点映射缓存 {training_id: [knowledge_point_names]}
        self._course_knowledge_map = {}
        # 所有课程的元信息 {training_id: {title, description, ...}}
        self._course_meta = {}

    # ============================================================
    # 1. 建立课程与知识点的关联（从数据库读取课程）
    # ============================================================
    def _load_courses(self):
        """从数据库加载所有实训项目（课程）"""
        if self._course_meta:
            return

        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute(
                'SELECT id, title, description, expected_steps, expected_outcomes, course_name '
                'FROM trainings ORDER BY course_name, title'
            )
            for row in cursor.fetchall():
                r = dict_from_row(row)
                tid = r['id']
                self._course_meta[tid] = {
                    'id': tid,
                    'title': r.get('title', ''),
                    'description': (r.get('description') or '')[:200],
                    'course_name': r.get('course_name', ''),
                    'expected_steps': (r.get('expected_steps') or ''),
                    'expected_outcomes': (r.get('expected_outcomes') or ''),
                }
        finally:
            cursor.close()

    def _extract_course_knowledge(self, training_id):
        """
        提取课程涉及的知识点。
        策略：
          1. 从课程标题/描述中关键词提取
          2. 如果有 LLM，用 LLM 提取
          3. 如果没有 LLM，用规则提取
        """
        if training_id in self._course_knowledge_map:
            return self._course_knowledge_map[training_id]

        course = self._course_meta.get(training_id)
        if not course:
            return []

        # 合并所有文本
        text = f"{course['title']} {course['description']} {course['expected_steps']} {course['expected_outcomes']}"

        # 如果有 LLM，用 LLM 提取
        if self.llm_service:
            try:
                prompt = f"""请分析以下课程的描述，提取课程涉及的核心知识点（2-5个）。
返回 JSON 格式：{{"knowledge_points": ["知识点1", "知识点2", ...]}}

课程标题：{course['title']}
课程描述：{(course.get('description') or '')[:500]}
预期成果：{(course.get('expected_outcomes') or '')[:500]}
"""
                messages = [{'role': 'user', 'content': prompt}]
                response = self.llm_service.chat_completion(messages, temperature=0.2, max_tokens=500)
                try:
                    start = response.find('{')
                    end = response.rfind('}') + 1
                    if start != -1 and end > start:
                        result = json.loads(response[start:end])
                        kps = result.get('knowledge_points', [])
                        self._course_knowledge_map[training_id] = kps
                        return kps
                except (json.JSONDecodeError, ValueError):
                    pass
            except Exception as e:
                print(f"[推荐] LLM 提取知识点失败: {e}")

        # 降级：从已有知识图谱匹配关键词
        kps = []
        if self.kg:
            all_nodes = self.kg.nodes.values()
            for node in all_nodes:
                name = node.get('name', '')
                if name and len(name) > 1 and name.lower() in text.lower():
                    kps.append(name)

        self._course_knowledge_map[training_id] = kps[:5]
        return kps[:5]

    # ============================================================
    # 2. 根据薄弱知识点推荐课程
    # ============================================================
    def recommend(self, weak_points, top_k=5):
        """
        根据薄弱知识点推荐课程。

        Args:
            weak_points: [{"knowledge_point": "...", "mastery": 0.3, ...}, ...]
            top_k: 推荐课程数量

        Returns:
            [{"course": {...}, "relevance_score": 0.85, "matched_points": [...], "reason": "..."}, ...]
        """
        self._load_courses()
        if not weak_points:
            return []

        weak_kp_names = [wp['knowledge_point'] for wp in weak_points]
        prereq_kp_names = set()

        # 1. 获取薄弱知识点的前置知识
        if self.kg:
            for wp in weak_points:
                prereqs = self.kg.get_prerequisites(wp['knowledge_point'])
                for p in prereqs:
                    prereq_kp_names.add(p['name'])

        # 2. 计算每个课程与薄弱知识点的匹配度
        recommendations = []
        for tid in self._course_meta:
            course_kps = self._extract_course_knowledge(tid)
            if not course_kps:
                continue

            course_kp_lower = [k.lower() for k in course_kps]

            # 匹配薄弱知识点
            direct_matches = []
            for wk in weak_kp_names:
                if wk.lower() in ' '.join(course_kp_lower):
                    direct_matches.append(wk)

            # 匹配前置知识
            prereq_matches = []
            for pk in prereq_kp_names:
                if pk.lower() in ' '.join(course_kp_lower):
                    prereq_matches.append(pk)

            # 计算相关性得分
            score = 0.0
            if direct_matches:
                score += len(direct_matches) * 0.4  # 直接匹配 0.4/个
            if prereq_matches:
                score += len(prereq_matches) * 0.2  # 前置匹配 0.2/个

            # 课程自身质量分（有完整描述加分）
            course = self._course_meta[tid]
            if course.get('description'):
                score += 0.1

            if score > 0:
                # 生成推荐理由
                reasons = []
                if direct_matches:
                    reasons.append(f"覆盖您的薄弱知识点: {', '.join(direct_matches)}")
                if prereq_matches:
                    reasons.append(f"涵盖您需要前置学习的: {', '.join(prereq_matches)}")

                recommendations.append({
                    'course': course,
                    'relevance_score': round(min(score, 1.0), 2),
                    'matched_points': {
                        'direct': direct_matches,
                        'prerequisite': prereq_matches,
                    },
                    'reason': '; '.join(reasons) if reasons else '与您的学习需求相关',
                })

        # 3. 排序并返回 Top-K
        recommendations.sort(key=lambda x: x['relevance_score'], reverse=True)
        return recommendations[:top_k]

    # ============================================================
    # 3. 智能推荐（含 LLM 解读）
    # ============================================================
    def recommend_with_explanation(self, weak_points, student_info=None, top_k=5):
        """
        智能推荐，包含 LLM 生成的详细解释。

        Args:
            weak_points: 薄弱知识点列表
            student_info: 学生信息（可选）

        Returns:
            {"recommendations": [...], "overall_analysis": "整体学习建议"}
        """
        recs = self.recommend(weak_points, top_k)
        if not recs:
            return {"recommendations": [], "overall_analysis": "暂无推荐课程"}

        # 用 LLM 生成学习建议
        analysis = ""
        if self.llm_service:
            weak_text = "\n".join([
                f"- {wp['knowledge_point']}（掌握度: {wp.get('mastery', '?')}）"
                for wp in weak_points[:5]
            ])
            rec_text = "\n".join([
                f"- {r['course']['title']}（匹配度: {r['relevance_score']}）"
                for r in recs[:3]
            ])

            prompt = f"""你是一名学习规划导师。请根据学生的薄弱知识点和推荐课程，给出个性化的学习建议。

【薄弱知识点】
{weak_text}

【推荐课程】
{rec_text}

请给出：
1. 总体学习路径建议（先学什么后学什么）
2. 学习优先级排序
3. 每个推荐课程应该重点关注什么

格式：简短精炼的段落，300字以内。
"""
            try:
                messages = [{'role': 'user', 'content': prompt}]
                analysis = self.llm_service.chat_completion(
                    messages, temperature=0.5, max_tokens=800
                )
            except Exception:
                analysis = ""

        return {
            'recommendations': recs,
            'overall_analysis': analysis or '请根据推荐课程逐个学习，优先学习匹配度高的课程。',
        }

    # ============================================================
    # 4. 统计
    # ============================================================
    def get_stats(self):
        self._load_courses()
        return {
            'total_courses': len(self._course_meta),
            'mapped_courses': len(self._course_knowledge_map),
        }


# 全局单例
_rec_engine = None

def get_recommendation_engine(knowledge_graph=None, llm_service=None):
    global _rec_engine
    if _rec_engine is None:
        _rec_engine = RecommendationEngine(knowledge_graph, llm_service)
    return _rec_engine
