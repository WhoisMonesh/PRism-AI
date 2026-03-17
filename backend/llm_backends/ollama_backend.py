import httpx
from .base import LLMClient
from ..config import get_settings


class OllamaBackend(LLMClient):
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.ollama_base_url
        self.model = self.settings.ollama_model

    async def generate(self, prompt: str, temperature: float = 0.2, max_tokens: int = 4000) -> str:
        async with httpx.AsyncClient(timeout=float(self.settings.llm_timeout)) as client:
            try:
                resp = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                        }
                    }
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("response", "")
            except Exception as e:
                raise RuntimeError(f"Ollama generation failed: {e}")

    async def health_check(self) -> bool:
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
            except:
                return False

    def get_model_name(self) -> str:
        return self.model
