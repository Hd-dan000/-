# -*- coding: utf-8 -*-
"""
RAG 模块包

对外导出：
  - RAGEngine: RAG 检索引擎类
  - get_rag_engine: 获取单例引擎
  - get_spec_files_info: 获取规范文件信息
"""

from rag.engine import RAGEngine
from rag.engine import get_rag_engine, get_spec_files_info

__all__ = ['RAGEngine', 'get_rag_engine', 'get_spec_files_info']
