import httpx
import hmac
import hashlib
from typing import Optional
from .base import GitProvider
from ..config import get_settings
from ..models import ReviewResult, ReviewComment


class BitbucketProvider(GitProvider):
    def __init__(self):
        settings = get_settings()
        self.token = settings.bitbucket_token
        self.base_url = settings.bitbucket_base_url.rstrip("/")
        self.webhook_secret = settings.bitbucket_webhook_secret

    async def verify_webhook(self, payload: bytes, signature: str) -> bool:
        if not self.webhook_secret or not signature:
            return False

        mac = hmac.new(
            self.webhook_secret.encode(),
            msg=payload,
            digestmod=hashlib.sha256
        )
        expected = f"sha256={mac.hexdigest()}"
        return hmac.compare_digest(expected, signature)

    async def get_pr_diff(self, owner: str, repo: str, number: int) -> str:
        headers = {
            "Authorization": f"Bearer {self.token}",
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(
                f"{self.base_url}/repositories/{owner}/{repo}/pullrequests/{number}/diff",
                headers=headers
            )
            resp.raise_for_status()
            return resp.text

    async def get_pr_files(self, owner: str, repo: str, number: int) -> list[dict]:
        headers = {
            "Authorization": f"Bearer {self.token}",
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(
                f"{self.base_url}/repositories/{owner}/{repo}/pullrequests/{number}/diffstat",
                headers=headers
            )
            resp.raise_for_status()
            data = resp.json()
            return [{"filename": item["new"]["path"]} for item in data.get("values", [])]

    async def post_pr_comment(self, owner: str, repo: str, number: int, body: str) -> None:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            await client.post(
                f"{self.base_url}/repositories/{owner}/{repo}/pullrequests/{number}/comments",
                headers=headers,
                json={"content": {"raw": body}}
            )

    async def post_inline_comments(
        self, owner: str, repo: str, number: int, comments: list[ReviewComment]
    ) -> None:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            for comment in comments:
                if comment.line is not None:
                    await client.post(
                        f"{self.base_url}/repositories/{owner}/{repo}/pullrequests/{number}/comments",
                        headers=headers,
                        json={
                            "content": {"raw": self._format_comment(comment)},
                            "inline": {
                                "path": comment.path,
                                "to": comment.line
                            }
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
        body = f"**AI Review Score: {result.score}/100**\n\n{result.summary}"
        await self.post_pr_comment(owner, repo, number, body)

    async def add_labels(self, owner: str, repo: str, number: int, labels: list[str]) -> None:
        pass

    async def health_check(self) -> bool:
        headers = {
            "Authorization": f"Bearer {self.token}",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(f"{self.base_url}/user", headers=headers)
                return resp.status_code == 200
            except:
                return False

    def _format_comment(self, comment: ReviewComment) -> str:
        msg = f"**{comment.severity.value.upper()}** [{comment.category.value}]\n\n{comment.message}"
        if comment.suggestion:
            msg += f"\n\n**Suggestion:**\n{comment.suggestion}"
        return msg
