import json
import re
import time

import httpx

from app.core.config import get_settings

settings = get_settings()


_summary_system_prompt = """
你是一个专业的资讯总结助手，能够帮助用户快速了解文章内容，也善于提取文章要点。

你的任务是，基于文章的标题和内容，生成以下两部分内容：
1. 生成一个简短的摘要，不超过50个字符，用来让用户了解文章在说什么，不要分段。
2. 生成一个详细的文章导读，包含文章内容的重点内容和关键信息，让用户不需要通读原文，也可以了解文章的核心内容。用<p>标签标记段落，不要使用其它HTML标签。

在生成上述内容的过程中，注意下列要求：
- 内容都需要用中文来描述，不要使用Markdown标记
- 不需要“本文讲述了...”或“作者主要介绍了...”等类似引导性的开头，请直接讲述内容

输出格式：
输出JSON格式的数据，包含两个字段：
- `short_summary`：文本类型，简短摘要
- `quick_read`：文本类型，文章导读
"""

class LLMService:
    def __init__(self) -> None:
        self.api_key = settings.llm_api_key
        self.base_url = settings.llm_base_url.rstrip('/')
        self.model = settings.llm_model

    def summarize_article(self, title: str, content: str) -> tuple[str, str]:
        if not self.api_key:
            raise Exception("API key not configured")

        payload = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': _summary_system_prompt},
                {
                    'role': 'user',
                    'content': f'标题: {title}\n内容:\n{content}',
                },
            ],
            'temperature': 0.2,
            'response_format': {'type': 'json_object'},
        }
        headers = {'Authorization': f'Bearer {self.api_key}'}
        text = self._post_chat_once_with_retry(payload=payload, headers=headers, timeout=60)
        if not text:
            raise Exception("Failed to get response from LLM API")

        data = self._safe_load_json_object(text)
        if not data:
            raise Exception("Failed to parse LLM API response as JSON")

        return str(data.get('short_summary')), str(data.get('quick_read'))

    def deduplicate_by_llm(self, category_name: str, article_rows: list[dict]) -> list[dict]:
        if not article_rows:
            return []
        if not self.api_key:
            return [{'id': row['id'], 'duplicate_ids': []} for row in article_rows]

        prompt = (
            '你将收到同一分类下的一组文章摘要。请按语义去重。'
            '输出JSON数组，每个元素包含 id 与 duplicate_ids。'
            'id 为保留文章ID，duplicate_ids 为与其重复的其它ID数组。'
        )
        payload = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': '你是信息去重助手，只输出JSON数组。'},
                {
                    'role': 'user',
                    'content': f'分类: {category_name}\n数据: {json.dumps(article_rows, ensure_ascii=False)}\n{prompt}',
                },
            ],
            'temperature': 0,
            'response_format': {'type': 'json_object'},
        }
        headers = {'Authorization': f'Bearer {self.api_key}'}
        text = self._post_chat_once_with_retry(payload=payload, headers=headers, timeout=90)
        if not text:
            return [{'id': row['id'], 'duplicate_ids': []} for row in article_rows]

        result = self._safe_load_json_array(text)
        return result or [{'id': row['id'], 'duplicate_ids': []} for row in article_rows]

    def _post_chat_once_with_retry(self, payload: dict, headers: dict, timeout: int) -> str:
        for attempt in range(2):
            try:
                with httpx.Client(timeout=timeout) as client:
                    resp = client.post(f'{self.base_url}/chat/completions', json=payload, headers=headers)
                    resp.raise_for_status()
                    return str(resp.json()['choices'][0]['message']['content'])
            except (httpx.TimeoutException, httpx.RequestError, KeyError, ValueError, TypeError):
                if attempt == 0:
                    time.sleep(0.8)
                    continue
                return ''
        return ''

    @staticmethod
    def _safe_load_json_object(text: str) -> dict:
        cleaned = (text or '').strip()
        if not cleaned:
            return {}
        try:
            data = json.loads(cleaned)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            pass

        block = LLMService._extract_json_block(cleaned, '{', '}')
        if not block:
            return {}
        try:
            data = json.loads(block)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _safe_load_json_array(text: str) -> list[dict]:
        cleaned = (text or '').strip()
        if not cleaned:
            return []
        try:
            data = json.loads(cleaned)
            if isinstance(data, list):
                return [item for item in data if isinstance(item, dict)]
            return []
        except json.JSONDecodeError:
            pass

        block = LLMService._extract_json_block(cleaned, '[', ']')
        if not block:
            return []
        try:
            data = json.loads(block)
            if isinstance(data, list):
                return [item for item in data if isinstance(item, dict)]
            return []
        except json.JSONDecodeError:
            return []

    @staticmethod
    def _extract_json_block(text: str, left: str, right: str) -> str:
        # Prefer fenced code block payload.
        fenced = re.findall(r'```(?:json)?\s*([\s\S]*?)\s*```', text, flags=re.IGNORECASE)
        candidates = fenced + [text]
        for candidate in candidates:
            start = candidate.find(left)
            end = candidate.rfind(right)
            if start != -1 and end != -1 and end > start:
                return candidate[start : end + 1].strip()
        return ''
