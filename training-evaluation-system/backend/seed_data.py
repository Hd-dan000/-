# -*- coding: utf-8 -*-
"""生成并插入组织架构基础数据：学校、学院、班级、教师、学生、管理员"""
import pymysql
import hashlib
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='123456', charset='utf8mb4', database='信息')
cursor = conn.cursor()

# ============================================================
# 1. 清空旧数据（按外键顺序倒序）
# ============================================================
tables_in_order = ['teacherclasses', 'students', 'classes', 'teachers', 'colleges', 'schools']
for t in tables_in_order:
    cursor.execute(f'DELETE FROM {t}')
    cursor.execute(f'ALTER TABLE {t} AUTO_INCREMENT = 1')
conn.commit()
print('旧数据已清空，自增归零')

# ============================================================
# 2. 学校 - 1所
# ============================================================
cursor.execute(
    "INSERT INTO schools (school_code, school_name, province, city, address, contact_phone, description, is_active) "
    "VALUES (%s,%s,%s,%s,%s,%s,%s,1)",
    ('SCHOOL001', '岭南信息职业技术学院', '广东', '广州市',
     '广州市天河区科韵路16号', '020-88886666',
     '省属重点信息技术类高职院校，以培养数字化高技能人才为特色')
)
conn.commit()
print('[1] 学校插入完成')

# ============================================================
# 3. 学院 - 5个
# ============================================================
colleges = [
    ('IT',     '信息工程学院',         '下设软件技术、移动应用开发等专业'),
    ('AI',     '人工智能学院',         '聚焦人工智能技术应用与计算机视觉方向'),
    ('BIGDATA','大数据与云计算学院',   '主攻大数据分析与云平台运维'),
    ('NETSEC', '网络空间安全学院',     '涵盖网络技术与信息安全方向'),
    ('SE',     '软件工程学院',         '面向软件工程与系统架构方向'),
]
for ccode, cname, cdesc in colleges:
    cursor.execute(
        "INSERT INTO colleges (school_id, college_code, college_name, description, is_active) VALUES (1,%s,%s,%s,1)",
        (ccode, cname, cdesc)
    )
conn.commit()
print(f'[2] 学院共 {len(colleges)} 个')

# ============================================================
# 4. 教师 - 10人（务必在班级之前插入，班级要引用教师ID）
# ============================================================
teachers_raw = [
    (1, 'TCH202401', '赵明',  '男', '副教授', '13922110001', 'zhaoming@lnit.edu.cn'),
    (1, 'TCH202402', '钱丽',  '女', '讲师',   '13922110002', 'qianli@lnit.edu.cn'),
    (2, 'TCH202403', '孙伟',  '男', '副教授', '13922110003', 'sunwei@lnit.edu.cn'),
    (2, 'TCH202404', '周静',  '女', '讲师',   '13922110004', 'zhoujing@lnit.edu.cn'),
    (3, 'TCH202405', '吴强',  '男', '教授',   '13922110005', 'wuqiang@lnit.edu.cn'),
    (3, 'TCH202406', '郑雪',  '女', '讲师',   '13922110006', 'zhengxue@lnit.edu.cn'),
    (4, 'TCH202407', '王海',  '男', '副教授', '13922110007', 'wanghai@lnit.edu.cn'),
    (4, 'TCH202408', '冯琳',  '女', '讲师',   '13922110008', 'fenglin@lnit.edu.cn'),
    (5, 'TCH202409', '陈磊',  '男', '副教授', '13922110009', 'chenlei@lnit.edu.cn'),
    (5, 'TCH202410', '褚芳',  '女', '讲师',   '13922110010', 'chufang@lnit.edu.cn'),
]
for cid, tno, name, gender, title, phone, email in teachers_raw:
    pwd_hash = hashlib.sha256(tno[-4:].encode()).hexdigest()
    cursor.execute(
        "INSERT INTO teachers (college_id, school_id, teacher_no, name, gender, title, department, phone, email, password_hash, is_active) "
        "VALUES (%s,1,%s,%s,%s,%s,'岭南信息职业技术学院',%s,%s,%s,1)",
        (cid, tno, name, gender, title, phone, email, pwd_hash)
    )
conn.commit()
print(f'[3] 教师共 {len(teachers_raw)} 人（密码=工号后4位）')

# 读取出教师 ID 映射
cursor.execute('SELECT id, teacher_no FROM teachers')
teacher_id_map = {row[1]: row[0] for row in cursor.fetchall()}

# ============================================================
# 5. 班级 - 10个
# ============================================================
classes_data = [
    (1, 'SOFT2401', '软件2401班', '软件技术',              '2024', 'TCH202401'),
    (1, 'SOFT2402', '软件2402班', '软件技术',              '2024', 'TCH202402'),
    (2, 'AI2401',   '人工智能2401班', '人工智能技术应用',  '2024', 'TCH202403'),
    (2, 'AI2402',   '人工智能2402班', '人工智能技术应用',  '2024', 'TCH202404'),
    (3, 'BD2401',   '大数据2401班',  '大数据技术',         '2024', 'TCH202405'),
    (3, 'BD2402',   '大数据2402班',  '大数据技术',         '2024', 'TCH202406'),
    (4, 'NET2401',  '网络2401班',    '计算机网络技术',     '2024', 'TCH202407'),
    (4, 'NET2402',  '网络2402班',    '计算机网络技术',     '2024', 'TCH202408'),
    (5, 'SE2401',   '软工2401班',    '软件工程技术',        '2024', 'TCH202409'),
    (5, 'SE2402',   '软工2402班',    '软件工程技术',        '2024', 'TCH202410'),
]

for cid, ccode, cname, major, grade, tno in classes_data:
    start_id = teacher_id_map[tno]
    cursor.execute(
        "INSERT INTO classes (college_id, school_id, class_code, class_name, major, grade, create_teacher_id, is_active) "
        "VALUES (%s,1,%s,%s,%s,%s,%s,1)",
        (cid, ccode, cname, major, grade, start_id)
    )
conn.commit()
print(f'[4] 班级共 {len(classes_data)} 个')

# 读出班级 ID 映射
cursor.execute('SELECT id, class_code FROM classes')
class_id_map = {row[1]: row[0] for row in cursor.fetchall()}

# ============================================================
# 6. 教师-班级关联（每个班级挂该学院的所有教师）
# ============================================================
tc_cnt = 0
for cid, ccode, cname, major, grade, tno in classes_data:
    for cid2, tno2, *_ in teachers_raw:
        if cid2 == cid:
            cursor.execute(
                "INSERT IGNORE INTO teacherclasses (teacher_id, class_id, role) VALUES (%s,%s,'指导教师')",
                (teacher_id_map[tno2], class_id_map[ccode])
            )
            tc_cnt += 1
conn.commit()
print(f'[5] 教师-班级关联共 {tc_cnt} 条')

# ============================================================
# 7. 学生 - 200人（每班20人，10班×20=200）
# ============================================================
import random
random.seed(42)

surnames = '李王张刘陈杨赵黄周吴徐孙马朱胡林何郭罗梁宋郑谢韩唐冯于董程曹袁邓许傅沈曾彭吕苏卢蒋蔡贾丁魏薛叶阎余潘杜戴夏钟汪田任姜范方石姚谭廖邹熊金陆郝孔白崔康毛邱秦江史顾侯邵孟龙万段钱汤尹黎易常武乔贺赖龚文'

male_first = '伟强磊军勇明杰涛斌浩鹏飞超波辉刚健峰志文博俊毅宏凯宇轩辰昊然哲洋鑫瑞彬鸿霖航'
male_last = '文成平志海宇安'
female_first = '静丽芳秀娟英敏洁婷雪琳瑶欣怡娜慧燕霞梦雨悦思露琪蕾菲妍茜彤宁佳颖璇萌璐婧诗薇'
female_last = '云清蓉华芳莲'

used_names = set()

def make_student_name(is_male):
    for _ in range(500):
        s = random.choice(surnames)
        if random.random() < 0.45:
            given = random.choice(male_first if is_male else female_first)
            name = s + given
        elif random.random() < 0.85:
            g1 = random.choice(male_first if is_male else female_first)
            g2 = random.choice(male_last if is_male else female_last)
            name = s + g1 + g2
            if len(name) > 3:
                name = name[:3]
        else:
            pairs_m = ['子豪','天佑','俊杰','文博','志远','建国','国强','家伟','立峰','嘉豪']
            pairs_f = ['若萱','梦瑶','思琪','语彤','可欣','婉婷','美琳','嘉琪','芷晴','晓萱']
            pairs = random.choice(pairs_m if is_male else pairs_f)
            name = s + pairs
        if name not in used_names:
            used_names.add(name)
            return name
    return '李想' + str(len(used_names) + 1)

student_idx = 1
for ccode, cid in sorted(class_id_map.items()):
    for i in range(20):
        is_male = i < 12
        gender = '男' if is_male else '女'
        name = make_student_name(is_male)
        sno = f'2024{student_idx:04d}'
        phone = f'1{random.choice(["30","35","37","38","39","50","56","58","86","88","99"])}{random.randint(1000000,99999999):08d}'
        email = f'{sno}@lnit.edu.cn'
        pwd_hash = hashlib.sha256(sno[-4:].encode()).hexdigest()
        cursor.execute(
            "INSERT INTO students (class_id, school_id, student_no, name, gender, class_name, major, phone, email, password_hash, is_active) "
            "VALUES (%s,1,%s,%s,%s,%s,'',%s,%s,%s,1)",
            (cid, sno, name, gender, ccode, phone, email, pwd_hash)
        )
        student_idx += 1
        if student_idx % 100 == 1:
            conn.commit()
conn.commit()
print(f'[6] 学生共 {student_idx-1} 人（密码=学号后4位）')

# ============================================================
# 8. 管理员 - 1条
# ============================================================
admin_hash = hashlib.sha256(b'admin123').hexdigest()
cursor.execute(
    "INSERT INTO admins (username, password_hash, display_name, role, is_active) "
    "VALUES (%s,%s,%s,'super_admin',1) ON DUPLICATE KEY UPDATE password_hash=%s",
    ('admin', admin_hash, '系统管理员', admin_hash)
)
conn.commit()
print('[7] 管理员: admin / admin123')

# ============================================================
# 9. 验证
# ============================================================
cursor.execute('SELECT COUNT(*) FROM schools');       r1 = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM colleges');      r2 = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM classes');       r3 = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM teachers');      r4 = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM students');      r5 = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM admins');        r6 = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM teacherclasses'); r7 = cursor.fetchone()[0]

print('\n' + '='*55)
print('📊 数据验证')
print(f'  schools           => {r1}')
print(f'  colleges          => {r2}')
print(f'  classes           => {r3}')
print(f'  teachers          => {r4}')
print(f'  students          => {r5}')
print(f'  admins            => {r6}')
print(f'  teacherclasses    => {r7}')
print('='*55)

cursor.execute('''
    SELECT c.class_name, COUNT(s.id)
    FROM classes c LEFT JOIN students s ON c.id = s.class_id
    GROUP BY c.id ORDER BY c.id
''')
print('\n📋 班级学生分布:')
total = 0
for row in cursor.fetchall():
    print(f'  {row[0]:20} => {row[1]}人')
    total += row[1]
print(f'  {"合计":20} => {total}人')

cursor.execute('''
    SELECT cl.college_name, COUNT(t.id)
    FROM colleges cl LEFT JOIN teachers t ON cl.id = t.college_id
    GROUP BY cl.id ORDER BY cl.id
''')
print('\n📋 学院教师分布:')
for row in cursor.fetchall():
    print(f'  {row[0]:20} => {row[1]}人')

cursor.execute('SELECT student_no, name, gender, class_name FROM students LIMIT 10')
print('\n📋 学生样本(前10):')
for row in cursor.fetchall():
    print(f'  {row[0][-4:]}  {row[1]}  {row[2]}  {row[3]}')

cursor.execute('SELECT teacher_no, name, title FROM teachers')
print('\n📋 教师列表:')
for row in cursor.fetchall():
    print(f'  {row[0]}  {row[1]:4}  {row[2]}')

cursor.close()
conn.close()
print('\n✅ 全部数据插入完成！')
