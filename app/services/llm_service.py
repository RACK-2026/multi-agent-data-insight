"""
LLM 统一调用层 - 支持豆包/OpenAI/Custom 多模型切换
"""
import json
from typing import Any, AsyncGenerator, Optional
from openai import AsyncOpenAI
from app.config import settings


class LLMService:
    """统一LLM调用服务"""

    def __init__(self):
        self._client: Optional[AsyncOpenAI] = None
        self._init_client()

    def _init_client(self):
        """根据配置初始化LLM客户端"""
        if settings.LLM_PROVIDER == "doubao":
            # 豆包/火山引擎
            base_url = settings.LLM_BASE_URL or "https://ark.cn-beijing.volces.com/api/v3"
            api_key = settings.LLM_API_KEY or ""
        elif settings.LLM_PROVIDER == "openai":
            base_url = settings.LLM_BASE_URL or "https://api.openai.com/v1"
            api_key = settings.LLM_API_KEY or ""
        else:
            base_url = settings.LLM_BASE_URL or ""
            api_key = settings.LLM_API_KEY or ""

        if api_key:
            self._client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url,
            )

    def is_available(self) -> bool:
        """检查LLM是否可用"""
        return self._client is not None

    async def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = None,
        max_tokens: int = None,
        response_format: dict = None,
    ) -> str:
        """
        LLM聊天调用

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            temperature: 温度参数
            max_tokens: 最大Token数
            response_format: 响应格式（如 {"type": "json_object"}）

        Returns:
            str: LLM响应文本
        """
        if not self.is_available():
            return "[LLM未配置] 请设置 LLM_API_KEY"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        kwargs = {
            "model": settings.LLM_MODEL,
            "messages": messages,
            "temperature": temperature or settings.LLM_TEMPERATURE,
            "max_tokens": max_tokens or settings.LLM_MAX_TOKENS,
        }

        if response_format:
            kwargs["response_format"] = response_format

        try:
            response = await self._client.chat.completions.create(**kwargs)
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[LLM调用失败] {str(e)}"

    async def chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = None,
    ) -> dict:
        """
        LLM调用并返回JSON对象

        Returns:
            dict: 解析后的JSON
        """
        result = await self.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            response_format={"type": "json_object"},
        )

        if result.startswith("[LLM"):
            return {"error": result}

        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"raw": result, "error": "JSON解析失败"}


# 全局单例
llm_service = LLMService()

