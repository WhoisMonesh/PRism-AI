from .base import LLMClient
from .ollama_backend import OllamaBackend
from .ollama_cloud_backend import OllamaCloudBackend
from .vertex_backend import VertexBackend
from .bedrock_backend import BedrockBackend
from .openai_backend import OpenAIBackend
from ..config import get_settings


def get_llm_client() -> LLMClient:
    settings = get_settings()
    provider = settings.llm_provider

    if provider == "ollama":
        return OllamaBackend()
    elif provider == "ollama_cloud":
        return OllamaCloudBackend()
    elif provider == "vertex":
        return VertexBackend()
    elif provider == "bedrock":
        return BedrockBackend()
    elif provider == "openai":
        return OpenAIBackend()
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


__all__ = [
    "LLMClient",
    "get_llm_client",
    "OllamaBackend",
    "OllamaCloudBackend",
    "VertexBackend",
    "BedrockBackend",
    "OpenAIBackend",
]
