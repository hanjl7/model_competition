from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

import httpx

from models.schemas import ModelConfig


class BaseProvider(ABC):
    def __init__(self, config: ModelConfig):
        self.config = config

    @abstractmethod
    async def stream_chat(
        self, messages: list[dict], system_prompt: str = ""
    ) -> AsyncIterator[str]:
        """Stream chat completion responses."""
        ...
