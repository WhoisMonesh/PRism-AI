from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
from .config import get_settings
from .models import (
    ReviewRequest, HealthStatus, GitProvider as GitProviderEnum,
    PullRequestRef, PromptFeedback
)
from .core import ReviewEngine, PromptEvolution
from .git_providers import get_git_provider
from .llm_backends import get_llm_client

settings = get_settings()
app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

review_engine = ReviewEngine()
prompt_evolution = PromptEvolution()


@app.get("/")
async def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/api/v1/health")
async def health_check():
    llm_available = False
    try:
        llm = get_llm_client()
        llm_available = await llm.health_check()
    except:
        pass

    git_providers_status = {}
    for provider in ["github", "gitlab", "gitea", "bitbucket"]:
        try:
            if settings.get_git_token(provider):
                git_provider = get_git_provider(GitProviderEnum(provider))
                git_providers_status[provider] = await git_provider.health_check()
            else:
                git_providers_status[provider] = False
        except:
            git_providers_status[provider] = False

    overall_status = "healthy" if llm_available else "degraded"
    if not llm_available and not any(git_providers_status.values()):
        overall_status = "unhealthy"

    return HealthStatus(
        status=overall_status,
        llm_backend=settings.llm_provider,
        llm_available=llm_available,
        git_providers=git_providers_status,
        version=settings.app_version
    )


@app.post("/api/v1/review")
async def manual_review(request: ReviewRequest):
    try:
        result = await review_engine.execute_review(request)
        return result
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/settings")
async def get_settings_route():
    return settings.to_ui_dict()


@app.post("/api/v1/settings")
async def update_settings_route(updates: dict):
    try:
        settings.update(updates)
        return {"status": "updated", "settings": settings.to_ui_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/models")
async def list_models():
    return {
        "current_provider": settings.llm_provider,
        "current_model": settings.to_ui_dict()["model"],
        "available_providers": ["ollama", "ollama_cloud", "vertex", "bedrock", "openai"]
    }


@app.post("/api/v1/feedback")
async def submit_feedback(feedback: PromptFeedback):
    try:
        prompt_evolution.record_feedback(feedback)
        return {"status": "recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/feedback/stats/{tool}")
async def get_feedback_stats(tool: str):
    try:
        stats = prompt_evolution.get_feedback_stats(tool)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def process_github_webhook(payload: dict):
    action = payload.get("action")
    if action not in ("opened", "synchronize"):
        return

    pr_data = payload.get("pull_request", {})
    if not pr_data:
        return

    repo = payload["repository"]
    owner = repo["owner"]["login"]
    repo_name = repo["name"]
    pr_number = pr_data["number"]

    request = ReviewRequest(
        pr=PullRequestRef(
            provider=GitProviderEnum.GITHUB,
            owner=owner,
            repo=repo_name,
            number=pr_number
        ),
        tool="review"
    )

    try:
        result = await review_engine.execute_review(request)
        provider = get_git_provider(GitProviderEnum.GITHUB)

        if isinstance(result, str):
            await provider.post_pr_comment(owner, repo_name, pr_number, result)
        else:
            await provider.create_review(owner, repo_name, pr_number, result)
            if result.comments:
                await provider.post_inline_comments(owner, repo_name, pr_number, result.comments)
    except Exception as e:
        print(f"GitHub webhook processing failed: {e}")


async def process_gitlab_webhook(payload: dict):
    object_kind = payload.get("object_kind")
    if object_kind != "merge_request":
        return

    action = payload.get("object_attributes", {}).get("action")
    if action not in ("open", "update"):
        return

    mr = payload.get("object_attributes", {})
    project = payload.get("project", {})
    owner = project.get("namespace", "unknown")
    repo_name = project.get("name", "unknown")
    mr_number = mr.get("iid")

    request = ReviewRequest(
        pr=PullRequestRef(
            provider=GitProviderEnum.GITLAB,
            owner=owner,
            repo=repo_name,
            number=mr_number
        ),
        tool="review"
    )

    try:
        result = await review_engine.execute_review(request)
        provider = get_git_provider(GitProviderEnum.GITLAB)

        if isinstance(result, str):
            await provider.post_pr_comment(owner, repo_name, mr_number, result)
        else:
            await provider.create_review(owner, repo_name, mr_number, result)
    except Exception as e:
        print(f"GitLab webhook processing failed: {e}")


@app.post("/api/v1/webhook/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    raw = await request.body()
    sig = request.headers.get("X-Hub-Signature-256")

    provider = get_git_provider(GitProviderEnum.GITHUB)
    if not await provider.verify_webhook(raw, sig):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = json.loads(raw)
    event = request.headers.get("X-GitHub-Event")

    if event == "pull_request" and settings.auto_review_on_pr:
        background_tasks.add_task(process_github_webhook, payload)

    return JSONResponse({"status": "accepted"})


@app.post("/api/v1/webhook/gitlab")
async def gitlab_webhook(request: Request, background_tasks: BackgroundTasks):
    raw = await request.body()
    token = request.headers.get("X-Gitlab-Token")

    provider = get_git_provider(GitProviderEnum.GITLAB)
    if not await provider.verify_webhook(raw, token):
        raise HTTPException(status_code=401, detail="Invalid token")

    payload = json.loads(raw)

    if settings.auto_review_on_pr:
        background_tasks.add_task(process_gitlab_webhook, payload)

    return JSONResponse({"status": "accepted"})


@app.post("/api/v1/webhook/gitea")
async def gitea_webhook(request: Request):
    return JSONResponse({"status": "not_implemented"})


@app.post("/api/v1/webhook/bitbucket")
async def bitbucket_webhook(request: Request):
    return JSONResponse({"status": "not_implemented"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
