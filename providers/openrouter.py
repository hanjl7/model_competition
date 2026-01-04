import json
from collections.abc import AsyncIterator

import httpx

from models.schemas import ModelConfig

from .base import BaseProvider


class OpenRouterProvider(BaseProvider):
    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",
            },
            timeout=60.0,
            trust_env=True,  # 使用环境变量代理
        )

    async def stream_chat(
        self, messages: list[dict], system_prompt: str = ""
    ) -> AsyncIterator[str]:
        request_messages = []
        if system_prompt:
            request_messages.append({"role": "system", "content": system_prompt})
        request_messages.extend(messages)

        payload = {
            "model": self.config.model_id,
            "messages": request_messages,
            "stream": True,
        }

        async with self.client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        if chunk.get("choices") and chunk["choices"][0].get("delta"):
                            content = chunk["choices"][0]["delta"].get("content", "")
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue

    async def close(self):
        await self.client.aclose()
