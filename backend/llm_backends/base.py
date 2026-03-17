from abc import ABC, abstractmethod
from typing import Optional


class LLMClient(ABC):
    @abstractmethod
    async def generate(self, prompt: str, temperature: float = 0.2, max_tokens: int = 4000) -> str:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        pass
