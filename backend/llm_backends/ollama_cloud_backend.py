import httpx
from .base import LLMClient
from ..config import get_settings


class OllamaCloudBackend(LLMClient):
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.ollama_cloud_url or "https://api.ollama.cloud/v1"
        self.api_key = self.settings.ollama_cloud_api_key
        self.model = self.settings.ollama_cloud_model

    async def generate(self, prompt: str, temperature: float = 0.2, max_tokens: int = 4000) -> str:
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient(timeout=float(self.settings.llm_timeout)) as client:
            try:
                resp = await client.post(
                    f"{self.base_url}/generate",
                    headers=headers,
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
                raise RuntimeError(f"Ollama Cloud generation failed: {e}")

    async def health_check(self) -> bool:
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(f"{self.base_url}/health", headers=headers)
                return resp.status_code == 200
            except:
                return False

    def get_model_name(self) -> str:
        return self.model
