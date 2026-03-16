"""Git provider factory for PRism-AI."""
from __future__ import annotations
from typing import Any, Dict


def create_git_provider(config: Dict[str, Any]):
    """Factory: create a git provider from config."""
    provider_type = config.get("type", "github").lower()
    if provider_type == "github":
        from .github_provider import GitHubProvider
        return GitHubProvider(config)
    elif provider_type == "gitlab":
        from .gitlab_provider import GitLabProvider
        return GitLabProvider(config)
    else:
        raise ValueError(f"Unknown git provider type: {provider_type}")


__all__ = ["create_git_provider"]
