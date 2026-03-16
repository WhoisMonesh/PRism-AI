"""
LLM Backend Factory
Returns the correct LLM client based on LLM_PROVIDER setting.
Supports: ollama (local), ollama_cloud, vertex, bedrock, openai, litellm
"""
from __future__ import annotations
from .base import LLMClient
from ..config import settings


from typing import Any, Dict, Optional, Union

def get_llm_client(provider: Union[str, Dict[str, Any], None] = None) -> LLMClient:
    config: Dict[str, Any] = {}
    if isinstance(provider, dict):
        config = provider
        p = config.get("provider", settings.llm_provider)
    else:
        p = provider or settings.llm_provider

    if p == "ollama":
        from .ollama_backend import OllamaClient
        return OllamaClient(config=config, cloud=False)
    elif p == "ollama_cloud":
        from .ollama_backend import OllamaClient
        return OllamaClient(config=config, cloud=True)
    elif p == "vertex":
        from .vertex_backend import VertexClient
        return VertexClient(config=config)
    elif p == "bedrock":
        from .bedrock_backend import BedrockClient
        return BedrockClient(config=config)
    elif p == "openai" or p == "litellm":
        from .openai_backend import OpenAIClient
        return OpenAIClient(config=config)
    raise ValueError(f"Unknown LLM provider: {p}")


__all__ = ["get_llm_client", "LLMClient"]
