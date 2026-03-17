from .base import GitProvider
from .github_provider import GitHubProvider
from .gitlab_provider import GitLabProvider
from .gitea_provider import GiteaProvider
from .bitbucket_provider import BitbucketProvider
from ..models import GitProvider as GitProviderEnum


def get_git_provider(provider: GitProviderEnum) -> GitProvider:
    if provider == GitProviderEnum.GITHUB:
        return GitHubProvider()
    elif provider == GitProviderEnum.GITLAB:
        return GitLabProvider()
    elif provider == GitProviderEnum.GITEA:
        return GiteaProvider()
    elif provider == GitProviderEnum.BITBUCKET:
        return BitbucketProvider()
    else:
        raise ValueError(f"Unsupported git provider: {provider}")


__all__ = [
    "GitProvider",
    "get_git_provider",
    "GitHubProvider",
    "GitLabProvider",
    "GiteaProvider",
    "BitbucketProvider",
]
