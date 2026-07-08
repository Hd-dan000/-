# -*- coding: utf-8 -*-
"""
RAG 服务兼容性转发文件
========================
原 RAG 实现已迁移到 backend/rag/ 独立包。
此文件保留，避免历史 import 路径报错。

请优先使用新路径：
    from rag import RAGEngine, get_rag_engine, get_spec_files_info
"""

from rag import RAGEngine, get_rag_engine, get_spec_files_info

__all__ = ['RAGEngine', 'get_rag_engine', 'get_spec_files_info']
