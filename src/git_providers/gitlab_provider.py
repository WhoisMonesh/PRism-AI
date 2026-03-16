"""GitLab provider for PRism-AI - supports gitlab.com and self-hosted GitLab."""
from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional
import httpx

logger = logging.getLogger(__name__)


class GitLabProvider:
    """Interact with GitLab or self-hosted GitLab APIs (Merge Requests)."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self.token: str = config.get("token", "")
        self.base_url: str = config.get("base_url", "https://gitlab.com").rstrip("/")
        self.timeout: int = int(config.get("timeout", 30))
        self.webhook_secret: Optional[str] = config.get("webhook_secret")

    def _headers(self) -> Dict[str, str]:
        return {
            "PRIVATE-TOKEN": self.token,
            "Content-Type": "application/json",
        }

    def _api(self, path: str) -> str:
        return f"{self.base_url}/api/v4{path}"

    async def get_pr_diff(self, project_id: str, mr_iid: int) -> str:
        """Get MR diff as unified diff text."""
        url = self._api(f"/projects/{project_id}/merge_requests/{mr_iid}/diffs")
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, headers=self._headers())
            resp.raise_for_status()
            diffs = resp.json()
            result = []
            for d in diffs:
                result.append(f"--- a/{d['old_path']}\n+++ b/{d['new_path']}")
                result.append(d.get("diff", ""))
            return "\n".join(result)

    async def get_pr_info(self, project_id: str, mr_iid: int) -> Dict[str, Any]:
        url = self._api(f"/projects/{project_id}/merge_requests/{mr_iid}")
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, headers=self._headers())
            resp.raise_for_status()
            return resp.json()

    async def get_pr_files(self, project_id: str, mr_iid: int) -> List[str]:
        url = self._api(f"/projects/{project_id}/merge_requests/{mr_iid}/diffs")
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, headers=self._headers())
            resp.raise_for_status()
            return [d["new_path"] for d in resp.json()]

    async def post_mr_note(self, project_id: str, mr_iid: int, body: str) -> None:
        url = self._api(f"/projects/{project_id}/merge_requests/{mr_iid}/notes")
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=self._headers(), json={"body": body})
            resp.raise_for_status()

    async def post_inline_comment(
        self,
        project_id: str,
        mr_iid: int,
        body: str,
        base_sha: str,
        start_sha: str,
        head_sha: str,
        path: str,
        new_line: int,
    ) -> None:
        url = self._api(f"/projects/{project_id}/merge_requests/{mr_iid}/discussions")
        payload = {
            "body": body,
            "position": {
                "base_sha": base_sha,
                "start_sha": start_sha,
                "head_sha": head_sha,
                "position_type": "text",
                "new_path": path,
                "new_line": new_line,
            },
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=self._headers(), json=payload)
            resp.raise_for_status()

    def verify_webhook_signature(self, token_header: str) -> bool:
        if not self.webhook_secret:
            return True
        return token_header == self.webhook_secret
