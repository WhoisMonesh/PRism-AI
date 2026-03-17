from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal, Optional
import os


class Settings(BaseSettings):
    app_name: str = "PRism-AI"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="production", env="ENVIRONMENT")
    base_url: str = Field(default="http://localhost:8000", env="BASE_URL")

    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")

    github_webhook_secret: Optional[str] = Field(default=None, env="GITHUB_WEBHOOK_SECRET")
    github_token: Optional[str] = Field(default=None, env="GITHUB_TOKEN")
    github_base_url: str = Field(default="https://api.github.com", env="GITHUB_BASE_URL")

    gitlab_webhook_secret: Optional[str] = Field(default=None, env="GITLAB_WEBHOOK_SECRET")
    gitlab_token: Optional[str] = Field(default=None, env="GITLAB_TOKEN")
    gitlab_base_url: str = Field(default="https://gitlab.com", env="GITLAB_BASE_URL")

    gitea_webhook_secret: Optional[str] = Field(default=None, env="GITEA_WEBHOOK_SECRET")
    gitea_token: Optional[str] = Field(default=None, env="GITEA_TOKEN")
    gitea_base_url: Optional[str] = Field(default=None, env="GITEA_URL")

    bitbucket_webhook_secret: Optional[str] = Field(default=None, env="BITBUCKET_WEBHOOK_SECRET")
    bitbucket_token: Optional[str] = Field(default=None, env="BITBUCKET_TOKEN")
    bitbucket_base_url: str = Field(default="https://api.bitbucket.org/2.0", env="BITBUCKET_BASE_URL")

    llm_provider: Literal["ollama", "ollama_cloud", "vertex", "bedrock", "openai"] = Field(
        default="ollama", env="LLM_PROVIDER"
    )
    llm_temperature: float = Field(default=0.2, env="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=4096, env="LLM_MAX_TOKENS")
    llm_timeout: int = Field(default=180, env="LLM_TIMEOUT")

    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama3.1", env="OLLAMA_MODEL")
    ollama_fallback_model: str = Field(default="qwen2.5-coder", env="OLLAMA_FALLBACK_MODEL")

    ollama_cloud_url: Optional[str] = Field(default=None, env="OLLAMA_CLOUD_URL")
    ollama_cloud_api_key: Optional[str] = Field(default=None, env="OLLAMA_CLOUD_API_KEY")
    ollama_cloud_model: str = Field(default="llama3.1", env="OLLAMA_CLOUD_MODEL")

    vertex_project_id: Optional[str] = Field(default=None, env="VERTEX_PROJECT_ID")
    vertex_location: str = Field(default="us-central1", env="VERTEX_LOCATION")
    vertex_model: str = Field(default="gemini-1.5-pro", env="VERTEX_MODEL")
    vertex_credentials_path: Optional[str] = Field(default=None, env="VERTEX_CREDENTIALS_PATH")

    bedrock_region: str = Field(default="us-east-1", env="BEDROCK_REGION")
    bedrock_model: str = Field(default="anthropic.claude-3-sonnet-20240229-v1:0", env="BEDROCK_MODEL")
    bedrock_access_key: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    bedrock_secret_key: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    bedrock_role_arn: Optional[str] = Field(default=None, env="BEDROCK_ROLE_ARN")

    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", env="OPENAI_API_BASE")
    openai_model: str = Field(default="gpt-4-turbo-preview", env="OPENAI_MODEL")

    supabase_url: Optional[str] = Field(default=None, env="VITE_SUPABASE_URL")
    supabase_key: Optional[str] = Field(default=None, env="VITE_SUPABASE_ANON_KEY")

    auto_review_on_pr: bool = Field(default=False, env="AUTO_REVIEW_ON_PR")
    auto_review_on_open: bool = Field(default=True, env="AUTO_REVIEW_ON_OPEN")
    auto_describe_on_open: bool = Field(default=True, env="AUTO_DESCRIBE_ON_OPEN")
    auto_label_on_open: bool = Field(default=True, env="AUTO_LABEL_ON_OPEN")
    auto_security_on_open: bool = Field(default=True, env="AUTO_SECURITY_ON_OPEN")
    inline_comments: bool = Field(default=True, env="INLINE_COMMENTS")
    collapse_suggestions: bool = Field(default=True, env="COLLAPSE_SUGGESTIONS")

    min_approval_score: int = Field(default=70, env="MIN_APPROVAL_SCORE")

    rbac_enabled: bool = Field(default=True, env="RBAC_ENABLED")
    policy_file: str = Field(default="policy.yaml", env="POLICY_FILE")

    notify_on_high_severity: bool = Field(default=True, env="NOTIFY_ON_HIGH_SEVERITY")
    database_url: str = Field(default="sqlite:///./prism_ai.db", env="DATABASE_URL")

    metrics_enabled: bool = Field(default=True, env="METRICS_ENABLED")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")

    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:8000", "http://localhost:3000"],
        env="CORS_ORIGINS"
    )

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"
    }

    def get_git_token(self, provider: str) -> Optional[str]:
        if provider == "github":
            return self.github_token
        elif provider == "gitlab":
            return self.gitlab_token
        elif provider == "gitea":
            return self.gitea_token
        elif provider == "bitbucket":
            return self.bitbucket_token
        return None

    def get_git_base_url(self, provider: str) -> Optional[str]:
        if provider == "github":
            return self.github_base_url
        elif provider == "gitlab":
            return self.gitlab_base_url
        elif provider == "gitea":
            return self.gitea_base_url
        elif provider == "bitbucket":
            return self.bitbucket_base_url
        return None

    def to_engine_config(self) -> dict:
        return {
            "llm_provider": self.llm_provider,
            "auto_review": self.auto_review_on_pr,
            "min_score": self.min_approval_score,
        }

    def to_ui_dict(self) -> dict:
        return {
            "llm_provider": self.llm_provider,
            "model": self._get_current_model(),
            "auto_review": self.auto_review_on_pr,
            "min_approval_score": self.min_approval_score,
            "auto_review_on_open": self.auto_review_on_open,
            "auto_describe_on_open": self.auto_describe_on_open,
            "auto_label_on_open": self.auto_label_on_open,
            "auto_security_on_open": self.auto_security_on_open,
            "inline_comments": self.inline_comments,
            "collapse_suggestions": self.collapse_suggestions,
            "rbac_enabled": self.rbac_enabled,
            "metrics_enabled": self.metrics_enabled,
        }

    def _get_current_model(self) -> str:
        if self.llm_provider == "ollama":
            return self.ollama_model
        elif self.llm_provider == "ollama_cloud":
            return self.ollama_cloud_model
        elif self.llm_provider == "vertex":
            return self.vertex_model
        elif self.llm_provider == "bedrock":
            return self.bedrock_model
        elif self.llm_provider == "openai":
            return self.openai_model
        return "unknown"

    def update(self, updates: dict) -> None:
        for key, value in updates.items():
            if hasattr(self, key):
                setattr(self, key, value)


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
