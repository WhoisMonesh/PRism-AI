from .base import LLMClient
from ..config import get_settings


class OpenAIBackend(LLMClient):
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.openai_api_key
        self.base_url = settings.openai_base_url
        self.model = settings.openai_model

        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url if self.base_url != "https://api.openai.com/v1" else None
            )
        except ImportError:
            raise RuntimeError("openai not installed. Run: pip install openai")

    async def generate(self, prompt: str, temperature: float = 0.2, max_tokens: int = 4000) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI generation failed: {e}")

    async def health_check(self) -> bool:
        try:
            models = await self.client.models.list()
            return len(list(models)) > 0
        except:
            return False

    def get_model_name(self) -> str:
        return self.model
