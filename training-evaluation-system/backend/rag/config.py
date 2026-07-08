# -*- coding: utf-8 -*-
"""
RAG 模块专属配置
"""
import os

from config import BASE_DIR


# 开发规范 JSONL 文件目录（指向项目根目录下的开发规范）
SPEC_DIR = os.path.join(BASE_DIR, '..', '..', '开发规范')

# RAG 缓存目录（存储向量化后的索引）
RAG_CACHE_DIR = os.path.join(BASE_DIR, 'rag', 'cache')
os.makedirs(RAG_CACHE_DIR, exist_ok=True)

# 检索参数
TOP_K = 5
SIMILARITY_THRESHOLD = 0.5

# 支持的规范文件列表
SPEC_FILES = [
    'Ant Design UI.jsonl',
    'Google java规范.jsonl',
    'google C++规范.jsonl',
    '华为C语言规范.jsonl',
    '尼尔森十大原则规范.jsonl',
    '阿里巴巴.Java规范jsonl',
]
