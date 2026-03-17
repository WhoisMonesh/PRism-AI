from pydantic import BaseModel, Field
from typing import Literal, Optional
from enum import Enum


class Severity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
    SUGGESTION = "suggestion"


class Category(str, Enum):
    BUG = "bug"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    STYLE = "style"
    DOCUMENTATION = "documentation"
    TEST = "test"
    GENERAL = "general"


class ReviewComment(BaseModel):
    path: str
    line: Optional[int] = None
    severity: Severity
    category: Category
    message: str
    suggestion: Optional[str] = None


class ReviewResult(BaseModel):
    score: int = Field(ge=0, le=100)
    approved: bool
    summary: str
    comments: list[ReviewComment] = []


class GitProvider(str, Enum):
    GITHUB = "github"
    GITLAB = "gitlab"
    GITEA = "gitea"
    BITBUCKET = "bitbucket"


class PullRequestRef(BaseModel):
    provider: GitProvider
    owner: str
    repo: str
    number: int


class ReviewRequest(BaseModel):
    pr: PullRequestRef
    tool: Literal[
        "review", "describe", "improve", "security",
        "changelog", "ask", "labels", "test_gen",
        "perf", "self_review", "auto_issue"
    ] = "review"
    question: Optional[str] = None


class WebhookEvent(BaseModel):
    provider: GitProvider
    event_type: str
    payload: dict


class PolicyRule(BaseModel):
    repo_pattern: str
    allowed_tools: list[str] = ["review", "describe"]
    allowed_llms: list[dict] = []
    allow_edit: bool = False
    min_score: int = 70
    blocked_patterns: list[str] = []
    severity_overrides: dict[str, str] = {}


class PromptFeedback(BaseModel):
    prompt_id: str
    tool: str
    was_helpful: bool
    human_feedback: Optional[str] = None
    score_before: Optional[int] = None
    score_after: Optional[int] = None


class HealthStatus(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    llm_backend: str
    llm_available: bool
    git_providers: dict[str, bool]
    version: str
