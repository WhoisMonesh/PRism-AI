"""OpenAI-compatible backend for PRism-AI (works with OpenAI, Azure OpenAI, and any OpenAI-compatible API)."""
from __future__ import annotations
import logging
from typing import Any, Dict, Optional
import httpx
from .base import BaseLLMClient

logger = logging.getLogger(__name__)


class OpenAIClient(BaseLLMClient):
    """OpenAI / Azure OpenAI / OpenAI-compatible backend."""

    def __init__(self, config: Dict[str, Any] = None) -> None:
        self.config = config or {}
        self.api_key: str = self.config.get("api_key", settings.openai_api_key)
        self.base_url: str = self.config.get("base_url", settings.openai_api_base)
        self.model: str = self.config.get("model", settings.openai_model)
        self.max_tokens: int = int(self.config.get("max_tokens", settings.llm_max_tokens))
        self.temperature: float = float(self.config.get("temperature", settings.llm_temperature))
        self.timeout: int = int(self.config.get("timeout", settings.llm_timeout))
        self.organization: Optional[str] = self.config.get("organization")

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.organization:
            headers["OpenAI-Organization"] = self.organization
        return headers

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            result = data["choices"][0]["message"]["content"].strip()
            logger.debug(f"[OpenAI] response length={len(result)}")
            return result

    async def list_models(self) -> list[str]:
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                data = response.json()
                return [m["id"] for m in data.get("data", [])]
            except Exception:
                return ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]

    async def health_check(self) -> bool:
        try:
            models = await self.list_models()
            return len(models) > 0
        except Exception as e:
            logger.warning(f"[OpenAI] health check failed: {e}")
            return False
