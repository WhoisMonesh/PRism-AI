import httpx
import hmac
import hashlib
from typing import Optional
from .base import GitProvider
from ..config import get_settings
from ..models import ReviewResult, ReviewComment, Severity


class GitHubProvider(GitProvider):
    def __init__(self):
        settings = get_settings()
        self.token = settings.github_token
        self.base_url = settings.github_base_url
        self.webhook_secret = settings.github_webhook_secret

    async def verify_webhook(self, payload: bytes, signature: str) -> bool:
        if not self.webhook_secret or not signature:
            return False

        algo, sig = signature.split("=", 1) if "=" in signature else ("sha256", signature)
        if algo != "sha256":
            return False

        mac = hmac.new(
            self.webhook_secret.encode(),
            msg=payload,
            digestmod=hashlib.sha256
        )
        expected = mac.hexdigest()
        return hmac.compare_digest(expected, sig)

    async def get_pr_diff(self, owner: str, repo: str, number: int) -> str:
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3.diff",
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/pulls/{number}",
                headers=headers
            )
            resp.raise_for_status()
            return resp.text

    async def get_pr_files(self, owner: str, repo: str, number: int) -> list[dict]:
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/pulls/{number}/files",
                headers=headers
            )
            resp.raise_for_status()
            return resp.json()

    async def post_pr_comment(self, owner: str, repo: str, number: int, body: str) -> None:
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/repos/{owner}/{repo}/issues/{number}/comments",
                headers=headers,
                json={"body": body}
            )
            resp.raise_for_status()

    async def post_inline_comments(
        self, owner: str, repo: str, number: int, comments: list[ReviewComment]
    ) -> None:
        pr_files = await self.get_pr_files(owner, repo, number)

        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            pr_resp = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/pulls/{number}",
                headers=headers
            )
            pr_resp.raise_for_status()
            pr_data = pr_resp.json()
            commit_sha = pr_data["head"]["sha"]

            review_comments = []
            for comment in comments:
                if comment.line is not None:
                    matching_file = next(
                        (f for f in pr_files if f["filename"] == comment.path), None
                    )
                    if matching_file:
                        review_comments.append({
                            "path": comment.path,
                            "position": comment.line,
                            "body": self._format_comment(comment)
                        })

            if review_comments:
                await client.post(
                    f"{self.base_url}/repos/{owner}/{repo}/pulls/{number}/reviews",
                    headers=headers,
                    json={
                        "commit_id": commit_sha,
                        "event": "COMMENT",
                        "comments": review_comments
                    }
                )

    async def create_review(
        self,
        owner: str,
        repo: str,
        number: int,
        result: ReviewResult,
        commit_sha: Optional[str] = None
    ) -> None:
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
        }

        if not commit_sha:
            async with httpx.AsyncClient(timeout=60.0) as client:
                pr_resp = await client.get(
                    f"{self.base_url}/repos/{owner}/{repo}/pulls/{number}",
                    headers=headers
                )
                pr_resp.raise_for_status()
                commit_sha = pr_resp.json()["head"]["sha"]

        event = "APPROVE" if result.approved else "REQUEST_CHANGES"
        body = f"**AI Review Score: {result.score}/100**\n\n{result.summary}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            await client.post(
                f"{self.base_url}/repos/{owner}/{repo}/pulls/{number}/reviews",
                headers=headers,
                json={
                    "commit_id": commit_sha,
                    "event": event,
                    "body": body
                }
            )

    async def add_labels(self, owner: str, repo: str, number: int, labels: list[str]) -> None:
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            await client.post(
                f"{self.base_url}/repos/{owner}/{repo}/issues/{number}/labels",
                headers=headers,
                json={"labels": labels}
            )

    async def create_issue(self, owner: str, repo: str, title: str, body: str, labels: Optional[list[str]] = None) -> dict:
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
        }
        payload = {"title": title, "body": body}
        if labels:
            payload["labels"] = labels
            
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/repos/{owner}/{repo}/issues",
                headers=headers,
                json=payload
            )
            resp.raise_for_status()
            return resp.json()

    async def health_check(self) -> bool:
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(f"{self.base_url}/user", headers=headers)
                return resp.status_code == 200
            except:
                return False

    def _format_comment(self, comment: ReviewComment) -> str:
        severity_emoji = {
            Severity.CRITICAL: "🔴",
            Severity.WARNING: "🟡",
            Severity.INFO: "🔵",
            Severity.SUGGESTION: "💡",
        }
        emoji = severity_emoji.get(comment.severity, "")
        msg = f"{emoji} **{comment.severity.value.upper()}** [{comment.category.value}]\n\n{comment.message}"
        if comment.suggestion:
            msg += f"\n\n**Suggestion:**\n{comment.suggestion}"
        return msg
