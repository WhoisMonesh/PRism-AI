"""Abstract LLM base class for PRism-AI"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    content: str
    model: str
    tokens_used: int = 0
    latency_ms: float = 0.0


class BaseLLMClient(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system: str = "", **kwargs) -> str: ...

    async def generate_structured(self, prompt: str, schema: dict, **kwargs) -> dict:
        import json
        raw = await self.generate(prompt + "\n\nRespond ONLY with valid JSON matching this schema: " + str(schema))
        try:
            return json.loads(raw)
        except Exception:
            return {"raw": raw}

    async def health_check(self) -> bool:
        return True

    async def list_models(self) -> list[str]:
        return []

# Alias for backward compatibility
LLMClient = BaseLLMClient
