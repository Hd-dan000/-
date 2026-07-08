import json
import time
import urllib.request
import urllib.error
import ssl
import hashlib
import hmac
import base64
from datetime import datetime, timezone

from config import (
    LLM_PROVIDER, LLM_API_PASSWORD, LLM_API_KEY, LLM_API_SECRET, LLM_APP_ID,
    LLM_API_BASE, LLM_MODEL, OLLAMA_HOST, OLLAMA_MODEL,
    EMBEDDING_PROVIDER, EMBEDDING_API_BASE, EMBEDDING_API_KEY, EMBEDDING_MODEL
)



class LLMService:

    def __init__(self):
        self.provider = LLM_PROVIDER
        self.api_password = LLM_API_PASSWORD
        self.api_key = LLM_API_KEY
        self.api_secret = LLM_API_SECRET
        self.app_id = LLM_APP_ID
        self.api_base = LLM_API_BASE
        self.model = LLM_MODEL
        self.ollama_host = OLLAMA_HOST
        self.ollama_model = OLLAMA_MODEL
        # Embedding 独立配置
        self.embedding_provider = EMBEDDING_PROVIDER
        self.embedding_api_base = EMBEDDING_API_BASE
        self.embedding_api_key = EMBEDDING_API_KEY
        self.embedding_model = EMBEDDING_MODEL
        self._context = ssl.create_default_context()
        self._context.check_hostname = False
        self._context.verify_mode = ssl.CERT_NONE

    def update_config(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def _generate_signature(self, host, date):
        signature_origin = f"host: {host}\ndate: {date}\nGET /v1/chat/completions HTTP/1.1"
        print(f"[DEBUG] 签名字符串:\n{signature_origin}")
        signature_sha = hmac.new(self.api_secret.encode('utf-8'),
                                 signature_origin.encode('utf-8'),
                                 hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode('utf-8')
        authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
        print(f"[DEBUG] Authorization: {authorization[:50]}...")
        return authorization

    def _make_request(self, url, data, headers, timeout=30):
        try:
            req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
            with urllib.request.urlopen(req, context=self._context, timeout=timeout) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            try:
                error_data = json.loads(e.read().decode('utf-8'))
                raise Exception(f"HTTP Error {e.code}: {error_data.get('error', {}).get('message', str(e))}")
            except:
                raise Exception(f"HTTP Error {e.code}: {str(e)}")
        except urllib.error.URLError as e:
            raise Exception(f"URL Error: {str(e)}")
        except Exception as e:
            raise Exception(f"Request Error: {str(e)}")

    def chat_completion(self, messages, model=None, temperature=0.7, max_tokens=2000):
        model = model or self.model
        if self.provider == 'ollama':
            url = f"{self.ollama_host.rstrip('/')}/api/chat"
            data = {
                'model': self.ollama_model,
                'messages': messages,
                'temperature': temperature
            }
            headers = {'Content-Type': 'application/json'}
            result = self._make_request(url, data, headers, timeout=60)
            content = ''
            if isinstance(result, dict) and 'message' in result:
                content = result['message'].get('content', '')
            return content
        else:
            url = f"{self.api_base.rstrip('/')}/chat/completions"
            data = {
                'model': model,
                'messages': messages,
                'temperature': temperature,
                'max_tokens': max_tokens
            }
            
            if self.api_password:
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.api_password}'
                }
            elif self.api_secret:
                import urllib.parse
                parsed_url = urllib.parse.urlparse(self.api_base)
                host = parsed_url.hostname
                date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
                authorization = self._generate_signature(host, date)
                params = {
                    'authorization': authorization,
                    'date': date,
                    'host': host
                }
                url = f"{url}?{urllib.parse.urlencode(params)}"
                data = {
                    'header': {'app_id': self.app_id},
                    'parameter': {'chat': {'domain': model, 'temperature': temperature, 'max_tokens': max_tokens}},
                    'payload': {'message': {'text': messages}}
                }
                headers = {'Content-Type': 'application/json'}
            else:
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.api_key}'
                }
            
            result = self._make_request(url, data, headers, timeout=60)
            if isinstance(result, dict):
                if 'header' in result and result.get('header', {}).get('code') == 0:
                    if 'payload' in result and 'choices' in result.get('payload', {}) and 'text' in result['payload'].get('choices', {}):
                        text_list = result['payload']['choices']['text']
                        return ''.join([item.get('content', '') for item in text_list])
                elif 'choices' in result and result['choices']:
                    return result['choices'][0]['message'].get('content', '')
            return str(result)

    def parse_submission(self, content, expected_steps, expected_outcomes):
        prompt = f"""你是一个软件实训评价专家，请分析以下实训提交内容，提取关键信息。

预期步骤：{expected_steps if expected_steps else '未指定'}

预期成果：{expected_outcomes if expected_outcomes else '未指定'}

提交内容：
{content[:5000]}

请按以下JSON格式返回分析结果：
{{
    "summary": "对提交内容的简要总结",
    "steps_completed": ["已完成的步骤列表"],
    "steps_missing": ["缺失的步骤列表"],
    "outcomes_achieved": ["已达成的成果"],
    "outcomes_missing": ["未达成的成果"],
    "logic_issues": ["发现的逻辑问题或漏洞"],
    "quality_assessment": "对整体质量的评价"
}}
"""
        messages = [{'role': 'user', 'content': prompt}]
        try:
            response = self.chat_completion(messages, temperature=0.3)
            try:
                start = response.find('{')
                end = response.rfind('}') + 1
                if start != -1 and end > start:
                    return json.loads(response[start:end])
                return json.loads(response)
            except (json.JSONDecodeError, ValueError):
                return {'summary': response, 'steps_completed': [], 'steps_missing': [],
                        'outcomes_achieved': [], 'outcomes_missing': [], 'logic_issues': [],
                        'quality_assessment': response}
        except Exception as e:
            return {'summary': f'解析失败: {str(e)}', 'steps_completed': [], 'steps_missing': [],
                    'outcomes_achieved': [], 'outcomes_missing': [], 'logic_issues': [],
                    'quality_assessment': '无法评估'}

    def evaluate_content(self, content, indicators):
        indicators_desc = "\n".join([f"{i['name']}: {i['description']}, 权重: {i['weight']}, 满分: {i['max_score']}" 
                                     for i in indicators])
        prompt = f"""你是一个软件实训评价专家，请根据以下评价指标对提交内容进行评分。

评价指标：
{indicators_desc}

提交内容：
{content[:5000]}

请按以下JSON格式返回评分结果：
{{
    "indicator_scores": [
        {{"indicator_name": "指标名称", "score": 得分, "reason": "评分理由"}}
    ],
    "overall_comment": "总体评价"
}}
"""
        messages = [{'role': 'user', 'content': prompt}]
        try:
            response = self.chat_completion(messages, temperature=0.3)
            try:
                start = response.find('{')
                end = response.rfind('}') + 1
                if start != -1 and end > start:
                    return json.loads(response[start:end])
                return json.loads(response)
            except (json.JSONDecodeError, ValueError):
                return {'indicator_scores': [], 'overall_comment': response}
        except Exception as e:
            return {'indicator_scores': [], 'overall_comment': f'评价失败: {str(e)}'}

    # ============================================================
    # Embedding 接口（用于 RAG 向量化）
    # ============================================================
    def get_embedding(self, text):
        """
        调用 LLM API 获取文本的向量嵌入。
        兼容 OpenAI Embedding API 和 Ollama Embedding API。
        """
        if not text or not text.strip():
            return None

        if self.provider == 'ollama':
            # Ollama embedding API
            url = f"{self.ollama_host.rstrip('/')}/api/embeddings"
            data = {
                'model': self.ollama_model,
                'prompt': text[:2000]  # 限制长度
            }
            headers = {'Content-Type': 'application/json'}
            try:
                result = self._make_request(url, data, headers, timeout=30)
                if isinstance(result, dict) and 'embedding' in result:
                    return result['embedding']
            except Exception as e:
                print(f"[LLM] Ollama embedding 失败: {e}")
                return None
        else:
            # OpenAI 兼容的 embedding API
            url = f"{self.api_base.rstrip('/')}/embeddings"
            data = {
                'model': 'text-embedding-v3',  # 讯飞的 embedding 模型名
                'input': text[:2000]
            }
            headers = {'Content-Type': 'application/json'}
            if self.api_password:
                headers['Authorization'] = f'Bearer {self.api_password}'
            elif self.api_key and not self.api_secret:
                headers['Authorization'] = f'Bearer {self.api_key}'
            try:
                result = self._make_request(url, data, headers, timeout=30)
                if isinstance(result, dict) and 'data' in result and len(result['data']) > 0:
                    return result['data'][0]['embedding']
            except Exception as e:
                print(f"[LLM] OpenAI embedding 失败: {e}")
                return None

        return None

    # ============================================================
    # 修改作业（核心方法）—— 基于开发规范的作业修改
    # ============================================================
    def modify_submission(self, content, modification_type='code', custom_requirements='', category_filter=None):
        """
        基于 RAG 检索到的开发规范，用 LLM 修改/优化学生作业。

        Args:
            content: 学生提交的作业内容（代码/文档文本）
            modification_type: 修改类型
                - 'code': 代码规范修改
                - 'ui': UI/UX 规范修改
                - 'all': 全部规范
                - 'custom': 自定义
            custom_requirements: 自定义修改要求
            category_filter: 指定使用的规范分类（如 'Ant Design UI'）

        Returns:
            {
                "modified_content": "修改后的内容",
                "changes": ["修改点列表"],
                "applied_specs": ["引用的规范条目"],
                "explanation": "修改说明"
            }
        """
        # 1. 从 RAG 检索相关规范
        from rag import get_rag_engine
        rag = get_rag_engine(self)

        context_text, retrieved_docs = rag.build_context(
            query=content[:3000],
            top_k=5,
            category_filter=category_filter
        )

        # 2. 构建修改 Prompt
        prompt_parts = []
        prompt_parts.append("你是一名专业的软件工程导师，请根据以下开发规范对学生的作业进行修改和优化。")
        prompt_parts.append("")

        if context_text:
            prompt_parts.append(context_text)
            prompt_parts.append("")
        else:
            prompt_parts.append("【注意】未检索到相关规范，请根据你的专业知识进行修改。")
            prompt_parts.append("")

        prompt_parts.append("【学生作业内容】")
        prompt_parts.append(content[:8000])  # 限制长度
        prompt_parts.append("")

        if modification_type == 'code':
            prompt_parts.append("【修改要求】")
            prompt_parts.append("1. 检查代码是否符合以上开发规范的编码风格要求")
            prompt_parts.append("2. 修正不符合规范的地方（命名、缩进、注释、代码结构等）")
            prompt_parts.append("3. 保持原有的功能逻辑不变")
            prompt_parts.append("4. 对每一处修改给出简短说明")
        elif modification_type == 'ui':
            prompt_parts.append("【修改要求】")
            prompt_parts.append("1. 检查 UI/UX 是否符合以上设计规范")
            prompt_parts.append("2. 提出界面改进建议（布局、色彩、交互等）")
            prompt_parts.append("3. 保持原有功能完整")
        elif modification_type == 'all':
            prompt_parts.append("【修改要求】")
            prompt_parts.append("1. 综合所有相关规范进行全面检查")
            prompt_parts.append("2. 修正代码风格、设计规范、可用性等方面的问题")
            prompt_parts.append("3. 保持原有功能逻辑不变")
            prompt_parts.append("4. 对每一处修改给出简短说明")

        if custom_requirements:
            prompt_parts.append("")
            prompt_parts.append("【自定义修改要求】")
            prompt_parts.append(custom_requirements)

        prompt_parts.append("")
        prompt_parts.append("【输出格式要求】")
        prompt_parts.append("请按以下 JSON 格式返回：")
        prompt_parts.append('''{
    "modified_content": "修改后的完整作业内容",
    "changes": [
        {"type": "modify/delete/add", "location": "修改位置描述", "description": "为什么这样修改", "spec_referenced": "引用的规范名称"}
    ],
    "applied_specs": ["用到的规范名称列表"],
    "explanation": "整体修改思路说明"
}''')

        full_prompt = "\n".join(prompt_parts)
        messages = [
            {'role': 'system', 'content': '你是一名严谨的软件工程导师，精通各种编程规范、设计规范、UI/UX 标准。你的任务是根据开发规范指导学生改进作业。请用中文回答，始终返回合法的 JSON 格式。'},
            {'role': 'user', 'content': full_prompt}
        ]

        # 3. 调用 LLM
        try:
            response = self.chat_completion(messages, temperature=0.3, max_tokens=4096)
            # 尝试解析 JSON
            try:
                start = response.find('{')
                end = response.rfind('}') + 1
                if start != -1 and end > start:
                    result = json.loads(response[start:end])
                else:
                    result = json.loads(response)

                # 确保字段完整
                if 'modified_content' not in result:
                    result['modified_content'] = content
                if 'changes' not in result:
                    result['changes'] = []
                if 'applied_specs' not in result:
                    result['applied_specs'] = [d['title'] for d in retrieved_docs]
                if 'explanation' not in result:
                    result['explanation'] = response[:500]

                return result

            except (json.JSONDecodeError, ValueError):
                # JSON 解析失败，返回原始响应
                return {
                    'modified_content': content,
                    'changes': [],
                    'applied_specs': [d['title'] for d in retrieved_docs],
                    'explanation': response[:1000],
                    'parse_error': True
                }

        except Exception as e:
            return {
                'modified_content': content,
                'changes': [],
                'applied_specs': [],
                'explanation': f'修改失败: {str(e)}',
                'error': str(e)
            }

    # ============================================================
    # 连接 RAG 引擎
    # ============================================================
    def init_rag(self):
        """获取 RAG 引擎单例并注入当前 LLM 实例（不再自动构建索引）"""
        from rag import get_rag_engine
        rag = get_rag_engine(self)
        rag.llm_service = self
        return rag

    def test_connection(self, prompt='你好，请简要介绍你自己。'):
        start = time.time()
        try:
            response = self.chat_completion([{'role': 'user', 'content': prompt}], max_tokens=100)
            latency = (time.time() - start) * 1000
            return True, response[:200] + ('...' if len(response) > 200 else ''), latency
        except Exception as e:
            latency = (time.time() - start) * 1000
            return False, str(e), latency

llm_service = LLMService()