"""
Ollama Backend - handles BOTH local Ollama and Ollama Cloud API.
Local:  http://ollama:11434  (no auth)
Cloud:  https://api.ollama.ai/v1  (Bearer token auth, OpenAI-compatible)
"""
from __future__ import annotations
import time
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from loguru import logger
from .base import LLMClient, LLMResponse
from ..config import settings


class OllamaClient(LLMClient):
    def __init__(self, config: dict = None, cloud: bool = False):
        self.config = config or {}
        self.cloud = cloud
        if cloud:
            self.base_url = self.config.get("base_url", settings.ollama_cloud_url).rstrip("/")
            self.model = self.config.get("model", settings.ollama_cloud_model)
            self.api_key = self.config.get("api_key", settings.ollama_cloud_api_key)
            logger.info(f"[Ollama] Cloud mode: {self.base_url} model={self.model}")
        else:
            self.base_url = self.config.get("base_url", settings.ollama_base_url).rstrip("/")
            self.model = self.config.get("model", settings.ollama_model)
            self.api_key = ""
            logger.info(f"[Ollama] Local mode: {self.base_url} model={self.model}")

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.cloud and self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    )
    async def generate(self, prompt: str, system: str = "", **kwargs) -> str:
        # Ollama Cloud uses OpenAI-compatible /chat/completions
        if self.cloud:
            return await self._chat_completions(prompt, system)
        # Local Ollama uses /api/generate
        return await self._local_generate(prompt, system)

    async def _local_generate(self, prompt: str, system: str) -> str:
        payload: dict = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config.get("temperature", settings.llm_temperature),
                "num_predict": self.config.get("max_tokens", settings.llm_max_tokens),
            },
        }
        if system:
            payload["system"] = system
        timeout = self.config.get("timeout", settings.llm_timeout)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{self.base_url}/api/generate",
                json=payload,
                headers=self._headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            result = data.get("response", "").strip()
            logger.debug(f"[Ollama-Local] tokens={data.get('eval_count', '?')}")
            return result

    async def _chat_completions(self, prompt: str, system: str) -> str:
        """Ollama Cloud - OpenAI-compatible endpoint."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.config.get("temperature", settings.llm_temperature),
            "max_tokens": self.config.get("max_tokens", settings.llm_max_tokens),
            "stream": False,
        }
        timeout = self.config.get("timeout", settings.llm_timeout)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self._headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            usage = data.get("usage", {})
            logger.debug(f"[Ollama-Cloud] tokens={usage.get('total_tokens', '?')}")
            return content

    async def list_models(self) -> list[str]:
        """Return available models - used by UI settings page."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                if self.cloud:
                    resp = await client.get(
                        f"{self.base_url}/models",
                        headers=self._headers(),
                    )
                else:
                    resp = await client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
                data = resp.json()
                if self.cloud:
                    return [m["id"] for m in data.get("data", [])]
                return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.warning(f"[Ollama] list_models failed: {e}")
            return []

    async def health_check(self) -> bool:
        """Returns True if Ollama is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                url = f"{self.base_url}/api/tags" if not self.cloud else f"{self.base_url}/models"
                resp = await client.get(url, headers=self._headers())
                return resp.status_code == 200
        except Exception:
            return False
