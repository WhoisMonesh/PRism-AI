from abc import ABC, abstractmethod
from typing import Optional
from ..models import ReviewResult, ReviewComment


class GitProvider(ABC):
    @abstractmethod
    async def verify_webhook(self, payload: bytes, signature: str) -> bool:
        pass

    @abstractmethod
    async def get_pr_diff(self, owner: str, repo: str, number: int) -> str:
        pass

    @abstractmethod
    async def get_pr_files(self, owner: str, repo: str, number: int) -> list[dict]:
        pass

    @abstractmethod
    async def post_pr_comment(self, owner: str, repo: str, number: int, body: str) -> None:
        pass

    @abstractmethod
    async def post_inline_comments(
        self, owner: str, repo: str, number: int, comments: list[ReviewComment]
    ) -> None:
        pass

    @abstractmethod
    async def create_review(
        self,
        owner: str,
        repo: str,
        number: int,
        result: ReviewResult,
        commit_sha: Optional[str] = None
    ) -> None:
        pass

    @abstractmethod
    async def add_labels(self, owner: str, repo: str, number: int, labels: list[str]) -> None:
        pass

    @abstractmethod
    async def create_issue(self, owner: str, repo: str, title: str, body: str, labels: Optional[list[str]] = None) -> dict:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass
