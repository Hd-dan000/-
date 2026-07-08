"""
为 AI 评阅报告模块生成覆盖“文档 / UI 截图 / 源代码”三类的测试数据。
基于 training_id=3，创建/更新多条 submissions，并写入模拟的 AI 分类评分，
使报告列表、分类查看、分类评分均可被端到端验证。
"""
import sqlite3
import json
import os
import shutil
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data.db')
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
TRAINING_ID = 3
CLASS_ID = 3
CLASS_NAME = 'AI2401'


def ensure_files():
    training_dir = os.path.join(UPLOAD_DIR, f'training_{TRAINING_ID}')
    os.makedirs(training_dir, exist_ok=True)

    doc_path = os.path.join(training_dir, 'report.md')
    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write('# 实训报告\n\n本次实训完成了需求分析、UI 设计与核心功能代码实现。\n')

    ui_path = os.path.join(training_dir, 'ui_design.png')
    logo_src = os.path.join(BASE_DIR, '..', 'frontend', 'src', 'logo.png')
    if os.path.exists(logo_src):
        shutil.copy(logo_src, ui_path)
    else:
        # 生成一个最小 1x1 PNG（橙色）
        minimal_png = bytes.fromhex(
            '89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489'
            '0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082'
        )
        with open(ui_path, 'wb') as f:
            f.write(minimal_png)

    code_path = os.path.join(training_dir, 'main.py')
    with open(code_path, 'w', encoding='utf-8') as f:
        f.write('def hello():\n    print("Hello, training evaluation!")\n\nif __name__ == "__main__":\n    hello()\n')

    return doc_path, ui_path, code_path


def make_files_json(doc_path, ui_path, code_path):
    files = []
    for path in (doc_path, ui_path, code_path):
        files.append({
            'filename': os.path.basename(path),
            'path': os.path.abspath(path),
            'size': os.path.getsize(path)
        })
    return json.dumps(files, ensure_ascii=False)


def make_evaluation_detail(category_scores):
    category_evaluation = {}
    for cat, score in category_scores.items():
        category_evaluation[cat] = {
            'score': score,
            'reason': f'AI 对 {cat} 的初步评价，得分为 {score}。'
        }
    return {
        'overall_comment': 'AI 综合评语：整体完成度良好，文档较完整，UI 设计基本符合要求，代码结构清晰但可进一步优化。',
        'category_evaluation': category_evaluation,
        'indicator_summary': [
            {'name': '逻辑结构', 'score': category_scores.get('document', 80), 'max_score': 100, 'reason': '文档逻辑清晰。'},
            {'name': '代码规范', 'score': category_scores.get('code', 78), 'max_score': 100, 'reason': '代码规范尚可。'},
            {'name': '功能实现', 'score': category_scores.get('code', 78), 'max_score': 100, 'reason': '功能基本实现。'}
        ],
        'code_annotations': [
            {'line_number': 1, 'type': 'suggestion', 'message': '建议添加函数文档字符串', 'suggestion': 'def hello():\n    """输出问候语"""'}
        ]
    }


def seed():
    doc_path, ui_path, code_path = ensure_files()
    files_json = make_files_json(doc_path, ui_path, code_path)
    now = datetime.now().isoformat()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 确保 training 3 可用且权重正确
    cur.execute(
        "UPDATE trainings SET status = 'not_started', category_weights = ? WHERE id = ?",
        (json.dumps({'document': 1 / 3, 'ui': 1 / 3, 'code': 1 / 3}, ensure_ascii=False), TRAINING_ID)
    )

    # 确保班级绑定存在
    cur.execute(
        "DELETE FROM training_classes WHERE training_id = ? AND class_id = ?",
        (TRAINING_ID, CLASS_ID)
    )
    cur.execute(
        "INSERT INTO training_classes (training_id, class_id, class_name) VALUES (?, ?, ?)",
        (TRAINING_ID, CLASS_ID, CLASS_NAME)
    )

    # 更新/插入 3 条测试提交，覆盖不同状态与评分
    test_students = [
        {'student_name': '孟峰', 'student_id': '20240001', 'category_scores': {'document': 82, 'ui': 78, 'code': 80}, 'status': 'submitted'},
        {'student_name': '李华', 'student_id': '20240002', 'category_scores': {'document': 75, 'ui': 80, 'code': 72}, 'status': 'evaluated'},
        {'student_name': '王强', 'student_id': '20240003', 'category_scores': {'document': 60, 'ui': 55, 'code': 58}, 'status': 'submitted'},
    ]

    for stu in test_students:
        eval_detail = make_evaluation_detail(stu['category_scores'])
        cur.execute(
            "SELECT id FROM submissions WHERE training_id = ? AND student_id = ?",
            (TRAINING_ID, stu['student_id'])
        )
        row = cur.fetchone()
        ai_total = round(sum(stu['category_scores'].values()) / len(stu['category_scores']), 1)
        final_score = ai_total if stu['status'] == 'evaluated' else None
        if row:
            cur.execute("""
                UPDATE submissions
                SET student_name = ?, class_id = ?, class_name = ?, files = ?, parsed_content = ?,
                    evaluation_detail = ?, ai_total_score = ?, final_score = ?, status = ?, updated_at = ?
                WHERE id = ?
            """, (
                stu['student_name'], CLASS_ID, CLASS_NAME, files_json, 'test content',
                json.dumps(eval_detail, ensure_ascii=False), ai_total, final_score, stu['status'], now, row['id']
            ))
        else:
            cur.execute("""
                INSERT INTO submissions (training_id, student_name, student_id, class_id, class_name, files, parsed_content,
                                         evaluation_detail, ai_total_score, final_score, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                TRAINING_ID, stu['student_name'], stu['student_id'], CLASS_ID, CLASS_NAME, files_json, 'test content',
                json.dumps(eval_detail, ensure_ascii=False), ai_total, final_score, stu['status'], now, now
            ))

    conn.commit()

    cur.execute("SELECT id, student_name, files, evaluation_detail FROM submissions WHERE training_id = ?", (TRAINING_ID,))
    for row in cur.fetchall():
        files = json.loads(row['files'])
        cats = [os.path.splitext(f['filename'])[1].lower() for f in files]
        print(f"submission_id={row['id']} student={row['student_name']} files={cats}")

    conn.close()
    print('测试数据准备完成')


if __name__ == '__main__':
    seed()
