"""
PRism-AI - Master Configuration
Supports: env vars, .env file, GCP/AWS/Vault secret managers
All secrets are NEVER hardcoded - always read from environment or secret manager
"""
from __future__ import annotations
from typing import Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── App ──────────────────────────────────────────────────────────────────
    app_name: str = "PRism-AI"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8080
    log_level: str = "INFO"
    environment: Literal["development", "staging", "production"] = "production"
    base_url: str = Field("", env="BASE_URL")  # public URL of this service

    # ── Self-Review (PRism-AI reviews its own repo) ───────────────────────────
    self_review_enabled: bool = Field(True, env="SELF_REVIEW_ENABLED")
    self_repo_owner: str = Field("WhoisMonesh", env="SELF_REPO_OWNER")
    self_repo_name: str = Field("PRism-AI", env="SELF_REPO_NAME")
    self_review_schedule: str = Field("0 2 * * *", env="SELF_REVIEW_SCHEDULE")  # cron
    self_review_branch: str = Field("main", env="SELF_REVIEW_BRANCH")

    # ── Evolution Engine ─────────────────────────────────────────────────────
    evolution_enabled: bool = Field(True, env="EVOLUTION_ENABLED")
    evolution_learn_from_feedback: bool = Field(True, env="EVOLUTION_LEARN_FROM_FEEDBACK")
    evolution_auto_improve_prompts: bool = Field(True, env="EVOLUTION_AUTO_IMPROVE_PROMPTS")
    evolution_metrics_retention_days: int = Field(90, env="EVOLUTION_METRICS_RETENTION_DAYS")

    # ── GitHub ────────────────────────────────────────────────────────────────
    github_token: str = Field("", env="GITHUB_TOKEN")
    github_webhook_secret: str = Field("", env="GITHUB_WEBHOOK_SECRET")
    github_app_id: str = Field("", env="GITHUB_APP_ID")
    github_app_private_key: str = Field("", env="GITHUB_APP_PRIVATE_KEY")
    github_api_url: str = Field("https://api.github.com", env="GITHUB_API_URL")  # override for GHE

    # ── GitLab ────────────────────────────────────────────────────────────────
    gitlab_token: str = Field("", env="GITLAB_TOKEN")
    gitlab_webhook_secret: str = Field("", env="GITLAB_WEBHOOK_SECRET")
    gitlab_url: str = Field("https://gitlab.com", env="GITLAB_URL")
    gitlab_ssl_verify: bool = Field(True, env="GITLAB_SSL_VERIFY")

    # ── Gitea (intranet) ──────────────────────────────────────────────────────
    gitea_token: str = Field("", env="GITEA_TOKEN")
    gitea_webhook_secret: str = Field("", env="GITEA_WEBHOOK_SECRET")
    gitea_url: str = Field("http://gitea:3000", env="GITEA_URL")
    gitea_ssl_verify: bool = Field(False, env="GITEA_SSL_VERIFY")

    # ── Bitbucket ─────────────────────────────────────────────────────────────
    bitbucket_token: str = Field("", env="BITBUCKET_TOKEN")
    bitbucket_workspace: str = Field("", env="BITBUCKET_WORKSPACE")
    bitbucket_webhook_secret: str = Field("", env="BITBUCKET_WEBHOOK_SECRET")

    # ── LLM Backend ───────────────────────────────────────────────────────────
    llm_provider: Literal["ollama", "ollama_cloud", "vertex", "bedrock", "openai", "litellm"] = Field(
        "ollama", env="LLM_PROVIDER"
    )
    llm_temperature: float = Field(0.2, env="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(4096, env="LLM_MAX_TOKENS")
    llm_timeout: int = Field(180, env="LLM_TIMEOUT")
    llm_retry_attempts: int = Field(3, env="LLM_RETRY_ATTEMPTS")
    max_diff_tokens: int = Field(12000, env="MAX_DIFF_TOKENS")
    max_files_per_review: int = Field(50, env="MAX_FILES_PER_REVIEW")

    # ── Ollama Local ──────────────────────────────────────────────────────────
    ollama_base_url: str = Field("http://ollama:11434", env="OLLAMA_BASE_URL")
    ollama_model: str = Field("llama3.1", env="OLLAMA_MODEL")
    ollama_fallback_model: str = Field("qwen2.5-coder", env="OLLAMA_FALLBACK_MODEL")

    # ── Ollama Cloud ──────────────────────────────────────────────────────────
    ollama_cloud_url: str = Field("https://api.ollama.ai/v1", env="OLLAMA_CLOUD_URL")
    ollama_cloud_api_key: str = Field("", env="OLLAMA_CLOUD_API_KEY")
    ollama_cloud_model: str = Field("llama3.1", env="OLLAMA_CLOUD_MODEL")
    ollama_cloud_enabled: bool = Field(False, env="OLLAMA_CLOUD_ENABLED")

    # ── Vertex AI (GCP) ───────────────────────────────────────────────────────
    vertex_project_id: str = Field("", env="VERTEX_PROJECT_ID")
    vertex_location: str = Field("us-central1", env="VERTEX_LOCATION")
    vertex_model: str = Field("gemini-1.5-pro", env="VERTEX_MODEL")
    vertex_service_account_json: str = Field("", env="VERTEX_SERVICE_ACCOUNT_JSON")
    vertex_use_workload_identity: bool = Field(False, env="VERTEX_USE_WORKLOAD_IDENTITY")

    # ── AWS Bedrock ───────────────────────────────────────────────────────────
    bedrock_region: str = Field("us-east-1", env="BEDROCK_REGION")
    bedrock_model: str = Field("anthropic.claude-3-5-sonnet-20241022-v2:0", env="BEDROCK_MODEL")
    bedrock_role_arn: str = Field("", env="BEDROCK_ROLE_ARN")
    aws_access_key_id: str = Field("", env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field("", env="AWS_SECRET_ACCESS_KEY")
    aws_session_token: str = Field("", env="AWS_SESSION_TOKEN")

    # ── OpenAI / Compatible ───────────────────────────────────────────────────
    openai_api_key: str = Field("", env="OPENAI_API_KEY")
    openai_api_base: str = Field("https://api.openai.com/v1", env="OPENAI_API_BASE")
    openai_model: str = Field("gpt-4o", env="OPENAI_MODEL")

    # ── Secret Manager ────────────────────────────────────────────────────────
    secret_manager: Literal["env", "gcp", "aws", "vault"] = Field("env", env="SECRET_MANAGER")
    gcp_secret_project: str = Field("", env="GCP_SECRET_PROJECT")
    aws_secrets_region: str = Field("us-east-1", env="AWS_SECRETS_REGION")
    vault_addr: str = Field("http://vault:8200", env="VAULT_ADDR")
    vault_token: str = Field("", env="VAULT_TOKEN")
    vault_path: str = Field("secret/prism-ai", env="VAULT_PATH")

    # ── RBAC / Policy ─────────────────────────────────────────────────────────
    policy_file: str = Field("policy.yaml", env="POLICY_FILE")
    rbac_enabled: bool = Field(True, env="RBAC_ENABLED")
    default_allowed_tools: list[str] = Field(
        default=["review", "describe"], env="DEFAULT_ALLOWED_TOOLS"
    )

    # ── Agent Behaviour ───────────────────────────────────────────────────────
    auto_review_on_open: bool = Field(True, env="AUTO_REVIEW_ON_OPEN")
    auto_describe_on_open: bool = Field(True, env="AUTO_DESCRIBE_ON_OPEN")
    auto_label_on_open: bool = Field(True, env="AUTO_LABEL_ON_OPEN")
    auto_security_on_open: bool = Field(True, env="AUTO_SECURITY_ON_OPEN")
    inline_comments: bool = Field(True, env="INLINE_COMMENTS")
    collapse_suggestions: bool = Field(True, env="COLLAPSE_SUGGESTIONS")

    # ── Notifications ─────────────────────────────────────────────────────────
    slack_webhook_url: str = Field("", env="SLACK_WEBHOOK_URL")
    teams_webhook_url: str = Field("", env="TEAMS_WEBHOOK_URL")
    notify_on_high_severity: bool = Field(True, env="NOTIFY_ON_HIGH_SEVERITY")

    # ── Metrics / Observability ───────────────────────────────────────────────
    metrics_enabled: bool = Field(True, env="METRICS_ENABLED")
    metrics_port: int = Field(9090, env="METRICS_PORT")
    sentry_dsn: str = Field("", env="SENTRY_DSN")

    # ── Storage ───────────────────────────────────────────────────────────────
    db_url: str = Field("sqlite:///./prism_ai.db", env="DATABASE_URL")
    redis_url: str = Field("", env="REDIS_URL")  # optional for caching


settings = Settings()


# ── Helper methods added to Settings ────────────────────────────────────────
from typing import Any, Dict, List

def _settings_to_engine_config(self) -> Dict[str, Any]:
    provider = self.llm_provider
    llm: Dict[str, Any] = {"provider": provider}
    if provider == "ollama":
        llm.update({"base_url": self.ollama_base_url, "model": self.ollama_model,
                    "temperature": self.llm_temperature, "max_tokens": self.llm_max_tokens,
                    "timeout": self.llm_timeout})
    elif provider == "ollama_cloud":
        llm.update({"base_url": self.ollama_cloud_url, "model": self.ollama_cloud_model,
                    "api_key": self.ollama_cloud_api_key, "temperature": self.llm_temperature,
                    "max_tokens": self.llm_max_tokens, "timeout": self.llm_timeout})
    elif provider == "vertex":
        llm.update({"project_id": self.vertex_project_id, "location": self.vertex_location,
                    "model": self.vertex_model,
                    "service_account_json": self.vertex_service_account_json,
                    "use_workload_identity": self.vertex_use_workload_identity,
                    "temperature": self.llm_temperature, "max_tokens": self.llm_max_tokens,
                    "timeout": self.llm_timeout})
    elif provider == "bedrock":
        llm.update({"region": self.bedrock_region, "model": self.bedrock_model,
                    "role_arn": self.bedrock_role_arn,
                    "aws_access_key_id": self.aws_access_key_id,
                    "aws_secret_access_key": self.aws_secret_access_key,
                    "aws_session_token": self.aws_session_token,
                    "timeout": self.llm_timeout})
    elif provider == "openai":
        llm.update({"api_key": self.openai_api_key, "base_url": self.openai_api_base,
                    "model": self.openai_model, "temperature": self.llm_temperature,
                    "max_tokens": self.llm_max_tokens, "timeout": self.llm_timeout})
    return {
        "llm": llm,
        "policy": {"rbac_enabled": self.rbac_enabled, "policy_file": self.policy_file},
        "max_diff_chars": self.max_diff_tokens * 4,
        "inline_comments": self.inline_comments,
    }

Settings.to_engine_config = _settings_to_engine_config


def _settings_to_ui_dict(self) -> Dict[str, Any]:
    return {
        "llm_provider": self.llm_provider,
        "llm_model": getattr(self, f"{self.llm_provider}_model",
                             self.ollama_model),
        "llm_base_url": getattr(self, f"{self.llm_provider}_base_url",
                                self.ollama_base_url),
        "auto_review": self.auto_review_on_open,
        "min_score_to_approve": 70,
        "inline_comments": self.inline_comments,
        "auto_label": self.auto_label_on_open,
        "auto_security": self.auto_security_on_open,
        "slack_webhook_url": self.slack_webhook_url,
        "teams_webhook_url": self.teams_webhook_url,
        "metrics_enabled": self.metrics_enabled,
        "environment": self.environment,
    }

Settings.to_ui_dict = _settings_to_ui_dict


def _settings_update(self, data: Dict[str, Any]) -> None:
    for key, value in data.items():
        if hasattr(self, key):
            object.__setattr__(self, key, value)

Settings.update = _settings_update


def _settings_get_git_token(self, provider: str) -> str:
    mapping = {
        "github": self.github_token,
        "gitlab": self.gitlab_token,
        "gitea": self.gitea_token,
        "bitbucket": self.bitbucket_token,
    }
    return mapping.get(provider, "")

Settings.get_git_token = _settings_get_git_token


def _settings_get_git_base_url(self, provider: str) -> str:
    mapping = {
        "github": self.github_api_url,
        "gitlab": self.gitlab_url,
        "gitea": self.gitea_url,
    }
    return mapping.get(provider, "")

Settings.get_git_base_url = _settings_get_git_base_url

# github_base_url alias
Settings.github_base_url = property(lambda self: self.github_api_url)

# cors_origins property
Settings.cors_origins = property(lambda self: ["*"])


_settings_instance: Optional[Settings] = None

def get_settings() -> Settings:
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance

