"""API routes for PRism-AI."""
from __future__ import annotations
import hashlib
import hmac
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel

from ..config import Settings, get_settings
from ..review_engine import ReviewEngine, ReviewResult
from ..git_providers import create_git_provider

router = APIRouter()
logger = logging.getLogger(__name__)


# ---------- Pydantic Models ----------

class ReviewRequest(BaseModel):
    repo: str  # owner/repo
    pr_number: int
    provider: str = "github"  # github | gitlab
    provider_base_url: Optional[str] = None
    token: Optional[str] = None


class SettingsUpdate(BaseModel):
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_base_url: Optional[str] = None
    auto_review: Optional[bool] = None
    min_score_to_approve: Optional[int] = None
    github_token: Optional[str] = None
    gitlab_token: Optional[str] = None
    github_api_url: Optional[str] = None
    gitlab_url: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    llm_backend: str
    llm_healthy: bool


# ---------- Health ----------

@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    engine = ReviewEngine(settings.to_engine_config())
    try:
        llm_ok = await engine.llm.health_check()
    except Exception:
        llm_ok = False
    return HealthResponse(
        status="ok",
        version="1.0.0",
        llm_backend=settings.llm_provider,
        llm_healthy=llm_ok,
    )


# ---------- Manual Review & Describe ----------

@router.post("/review", tags=["Review"])
async def trigger_review(
    req: ReviewRequest,
    settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    """Manually trigger a PR review."""
    owner, repo_name = req.repo.split("/", 1)
    git_config = {
        "type": req.provider,
        "token": req.token or settings.get_git_token(req.provider),
        "base_url": req.provider_base_url or settings.get_git_base_url(req.provider),
    }
    git = create_git_provider(git_config)

    try:
        diff = await git.get_pr_diff(owner, repo_name, req.pr_number)
        pr_info = await git.get_pr_info(owner, repo_name, req.pr_number)
        files = await git.get_pr_files(owner, repo_name, req.pr_number)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Git provider error: {e}")

    engine = ReviewEngine(settings.to_engine_config())
    result = await engine.review_pr(
        pr_number=req.pr_number,
        repo=req.repo,
        diff=diff,
        pr_title=pr_info.get("title", ""),
        pr_body=pr_info.get("body", ""),
        changed_files=files,
    )
    return _result_to_dict(result)

@router.post("/describe", tags=["Review"])
async def trigger_describe(
    req: ReviewRequest,
    settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    """Generate a PR description."""
    owner, repo_name = req.repo.split("/", 1)
    git_config = {
        "type": req.provider,
        "token": req.token or settings.get_git_token(req.provider),
        "base_url": req.provider_base_url or settings.get_git_base_url(req.provider),
    }
    git = create_git_provider(git_config)

    try:
        diff = await git.get_pr_diff(owner, repo_name, req.pr_number)
        files = await git.get_pr_files(owner, repo_name, req.pr_number)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Git provider error: {e}")

    engine = ReviewEngine(settings.to_engine_config())
    description = await engine.describe_pr(
        pr_number=req.pr_number,
        repo=req.repo,
        diff=diff,
        changed_files=files,
    )
    return {"description": description}


# ---------- Webhook ----------

@router.post("/webhook/github", tags=["Webhooks"])
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_github_event: str = Header(default=""),
    x_hub_signature_256: str = Header(default=""),
    settings: Settings = Depends(get_settings),
) -> Dict[str, str]:
    body = await request.body()
    # Verify signature
    if settings.github_webhook_secret:
        expected = "sha256=" + hmac.new(
            settings.github_webhook_secret.encode(), body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, x_hub_signature_256):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = await request.json()
    if x_github_event == "pull_request" and payload.get("action") in ("opened", "synchronize", "reopened"):
        background_tasks.add_task(_handle_github_pr, payload, settings)
    return {"status": "accepted"}


async def _handle_github_pr(payload: Dict[str, Any], settings: Settings) -> None:
    pr = payload["pull_request"]
    repo = payload["repository"]["full_name"]
    pr_number = pr["number"]
    owner, repo_name = repo.split("/", 1)

    git_config = {
        "type": "github",
        "token": settings.github_token,
        "base_url": settings.github_base_url,
        "webhook_secret": settings.github_webhook_secret,
    }
    git = create_git_provider(git_config)
    try:
        diff = await git.get_pr_diff(owner, repo_name, pr_number)
        files = await git.get_pr_files(owner, repo_name, pr_number)
        engine = ReviewEngine(settings.to_engine_config())
        result = await engine.review_pr(
            pr_number=pr_number,
            repo=repo,
            diff=diff,
            pr_title=pr.get("title", ""),
            pr_body=pr.get("body", ""),
            changed_files=files,
        )
        # Post review
        event = "APPROVE" if result.approved else "REQUEST_CHANGES"
        review_comments = [
            {
                "path": c.path,
                "line": c.line or 1,
                "side": "RIGHT",
                "body": f"**[{c.severity.upper()}] {c.category}**\n{c.message}" + (f"\n```suggestion\n{c.suggestion}\n```" if c.suggestion else ""),
            }
            for c in result.comments if c.path and c.line
        ]
        await git.post_pr_review(
            owner=owner,
            repo=repo_name,
            pr_number=pr_number,
            body=f"## PRism-AI Review\n\n**Score:** {result.score}/100\n\n{result.summary}",
            event=event,
            comments=review_comments or None,
        )
        if result.score >= 90:
            await git.add_label(owner, repo_name, pr_number, ["prism-ai: approved"])
        elif result.score < 50:
            await git.add_label(owner, repo_name, pr_number, ["prism-ai: needs-work"])
    except Exception as e:
        logger.error(f"[Webhook] Failed to process PR#{pr_number}: {e}")


# ---------- Settings API ----------

@router.get("/settings", tags=["Settings"])
async def get_current_settings(settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    return settings.to_ui_dict()


@router.post("/settings", tags=["Settings"])
async def update_settings(
    update: SettingsUpdate,
    settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    settings.update(update.model_dump(exclude_none=True))
    return settings.to_ui_dict()


@router.get("/models", tags=["Settings"])
async def list_models(settings: Settings = Depends(get_settings)) -> Dict[str, List[str]]:
    engine = ReviewEngine(settings.to_engine_config())
    try:
        models = await engine.llm.list_models()
    except Exception:
        models = []
    return {"models": models}


# ---------- Helpers ----------

def _result_to_dict(result: ReviewResult) -> Dict[str, Any]:
    return {
        "pr_number": result.pr_number,
        "repo": result.repo,
        "summary": result.summary,
        "score": result.score,
        "approved": result.approved,
        "comments": [
            {
                "path": c.path,
                "line": c.line,
                "severity": c.severity,
                "category": c.category,
                "message": c.message,
                "suggestion": c.suggestion,
            }
            for c in result.comments
        ],
    }
