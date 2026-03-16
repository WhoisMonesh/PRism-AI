"""GCP Vertex AI Backend - supports service account JSON and workload identity"""
from __future__ import annotations
import json
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from .base import LLMClient
from ..config import settings


class VertexClient(LLMClient):
    def __init__(self, config: dict = None):
        self.config = config or {}
        self._client = None
        self._model = self.config.get("model", settings.vertex_model)
        self._project = self.config.get("project_id", settings.vertex_project_id)
        self._location = self.config.get("location", settings.vertex_location)
        logger.info(f"[Vertex] project={self._project} model={self._model}")

    def _get_client(self):
        if self._client:
            return self._client
        import vertexai
        from vertexai.generative_models import GenerativeModel
        
        sa_json = self.config.get("service_account_json", settings.vertex_service_account_json)
        
        if sa_json:
            import google.auth
            from google.oauth2 import service_account
            creds = service_account.Credentials.from_service_account_info(
                json.loads(sa_json),
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            vertexai.init(project=self._project, location=self._location, credentials=creds)
        else:
            # Uses workload identity / ADC
            vertexai.init(project=self._project, location=self._location)
        self._client = GenerativeModel(self._model)
        return self._client

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def generate(self, prompt: str, system: str = "", **kwargs) -> str:
        import asyncio
        model = self._get_client()
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        
        temp = self.config.get("temperature", settings.llm_temperature)
        max_tokens = self.config.get("max_tokens", settings.llm_max_tokens)
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(
                full_prompt,
                generation_config={"temperature": temp, "max_output_tokens": max_tokens}
            )
        )
        result = response.text.strip()
        logger.debug(f"[Vertex] response length={len(result)}")
        return result

    async def list_models(self) -> list[str]:
        return ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.0-pro"]

    async def health_check(self) -> bool:
        try:
            self._get_client()
            return True
        except Exception as e:
            logger.warning(f"[Vertex] health_check failed: {e}")
            return False
