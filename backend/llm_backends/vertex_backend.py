from .base import LLMClient
from ..config import get_settings
import os


class VertexBackend(LLMClient):
    def __init__(self):
        settings = get_settings()
        self.project_id = settings.vertex_project_id
        self.location = settings.vertex_location
        self.model_name = settings.vertex_model

        if settings.vertex_credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.vertex_credentials_path

        try:
            from google.cloud import aiplatform
            from vertexai.generative_models import GenerativeModel
            aiplatform.init(project=self.project_id, location=self.location)
            self.model = GenerativeModel(self.model_name)
        except ImportError:
            raise RuntimeError("google-cloud-aiplatform not installed. Run: pip install google-cloud-aiplatform")

    async def generate(self, prompt: str, temperature: float = 0.2, max_tokens: int = 4000) -> str:
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                }
            )
            return response.text
        except Exception as e:
            raise RuntimeError(f"Vertex AI generation failed: {e}")

    async def health_check(self) -> bool:
        try:
            test_response = self.model.generate_content("test", generation_config={"max_output_tokens": 10})
            return bool(test_response.text)
        except:
            return False

    def get_model_name(self) -> str:
        return self.model_name
