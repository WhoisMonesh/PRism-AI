"""GitHub provider for PRism-AI - supports github.com and GitHub Enterprise."""
from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional
import httpx

logger = logging.getLogger(__name__)


class GitHubProvider:
    """Interact with GitHub or GitHub Enterprise APIs."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self.token: str = config.get("token", "")
        self.base_url: str = config.get("base_url", "https://api.github.com").rstrip("/")
        self.timeout: int = int(config.get("timeout", 30))
        self.webhook_secret: Optional[str] = config.get("webhook_secret")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(
                url,
                headers={**self._headers(), "Accept": "application/vnd.github.v3.diff"},
            )
            resp.raise_for_status()
            return resp.text

    async def get_pr_info(self, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, headers=self._headers())
            resp.raise_for_status()
            return resp.json()

    async def get_pr_files(self, owner: str, repo: str, pr_number: int) -> List[str]:
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/files"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, headers=self._headers())
            resp.raise_for_status()
            return [f["filename"] for f in resp.json()]

    async def post_review_comment(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        body: str,
        commit_id: str,
        path: str,
        line: int,
    ) -> None:
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/comments"
        payload = {"body": body, "commit_id": commit_id, "path": path, "line": line, "side": "RIGHT"}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=self._headers(), json=payload)
            resp.raise_for_status()

    async def post_pr_review(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        body: str,
        event: str = "COMMENT",  # APPROVE | REQUEST_CHANGES | COMMENT
        comments: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        payload: Dict[str, Any] = {"body": body, "event": event}
        if comments:
            payload["comments"] = comments
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=self._headers(), json=payload)
            resp.raise_for_status()

    async def add_label(self, owner: str, repo: str, pr_number: int, labels: List[str]) -> None:
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{pr_number}/labels"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=self._headers(), json={"labels": labels})
            resp.raise_for_status()

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        import hmac, hashlib
        if not self.webhook_secret:
            return True
        expected = "sha256=" + hmac.new(
            self.webhook_secret.encode(), payload, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
