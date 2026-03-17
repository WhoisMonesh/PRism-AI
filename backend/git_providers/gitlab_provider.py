import httpx
import hmac
import hashlib
from typing import Optional
from .base import GitProvider
from ..config import get_settings
from ..models import ReviewResult, ReviewComment, Severity


class GitLabProvider(GitProvider):
    def __init__(self):
        settings = get_settings()
        self.token = settings.gitlab_token
        self.base_url = settings.gitlab_base_url.rstrip("/")
        self.webhook_secret = settings.gitlab_webhook_secret

    async def verify_webhook(self, payload: bytes, signature: str) -> bool:
        if not self.webhook_secret or not signature:
            return False
        return hmac.compare_digest(self.webhook_secret, signature)

    async def get_pr_diff(self, owner: str, repo: str, number: int) -> str:
        project_id = f"{owner}/{repo}".replace("/", "%2F")
        headers = {
            "PRIVATE-TOKEN": self.token,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(
                f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{number}/changes",
                headers=headers
            )
            resp.raise_for_status()
            data = resp.json()
            diff = ""
            for change in data.get("changes", []):
                diff += change.get("diff", "")
            return diff

    async def get_pr_files(self, owner: str, repo: str, number: int) -> list[dict]:
        project_id = f"{owner}/{repo}".replace("/", "%2F")
        headers = {
            "PRIVATE-TOKEN": self.token,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(
                f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{number}/changes",
                headers=headers
            )
            resp.raise_for_status()
            data = resp.json()
            return [{"filename": change["new_path"]} for change in data.get("changes", [])]

    async def post_pr_comment(self, owner: str, repo: str, number: int, body: str) -> None:
        project_id = f"{owner}/{repo}".replace("/", "%2F")
        headers = {
            "PRIVATE-TOKEN": self.token,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            await client.post(
                f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{number}/notes",
                headers=headers,
                json={"body": body}
            )

    async def post_inline_comments(
        self, owner: str, repo: str, number: int, comments: list[ReviewComment]
    ) -> None:
        project_id = f"{owner}/{repo}".replace("/", "%2F")
        headers = {
            "PRIVATE-TOKEN": self.token,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            mr_resp = await client.get(
                f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{number}",
                headers=headers
            )
            mr_resp.raise_for_status()
            mr_data = mr_resp.json()
            commit_sha = mr_data["sha"]

            for comment in comments:
                if comment.line is not None:
                    await client.post(
                        f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{number}/discussions",
                        headers=headers,
                        json={
                            "body": self._format_comment(comment),
                            "position": {
                                "base_sha": mr_data["diff_refs"]["base_sha"],
                                "start_sha": mr_data["diff_refs"]["start_sha"],
                                "head_sha": commit_sha,
                                "position_type": "text",
                                "new_path": comment.path,
                                "new_line": comment.line,
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
        project_id = f"{owner}/{repo}".replace("/", "%2F")
        headers = {
            "PRIVATE-TOKEN": self.token,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            await client.put(
                f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{number}",
                headers=headers,
                json={"labels": ",".join(labels)}
            )

    async def health_check(self) -> bool:
        headers = {
            "PRIVATE-TOKEN": self.token,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(f"{self.base_url}/api/v4/user", headers=headers)
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
