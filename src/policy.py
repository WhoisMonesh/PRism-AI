"""
PRism-AI RBAC Policy Engine
Supports: global policy.yaml, per-repo .prism.yml, role-based tool access
"""
from __future__ import annotations
import re
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from loguru import logger
from .config import settings

ALL_TOOLS = [
    "review", "describe", "improve", "security",
    "changelog", "ask", "labels", "test_gen", "performance", "self_review"
]


@dataclass
class RepoPolicy:
    allowed_tools: List[str] = field(default_factory=lambda: ["review", "describe"])
    excluded_files: List[str] = field(default_factory=list)
    min_score_to_approve: int = 70
    allowed_llm_providers: list[str] = field(default_factory=lambda: ["ollama"])
    allowed_llm_models: list[str] = field(default_factory=list)
    allow_edit: bool = False
    allow_auto_merge: bool = False
    required_role_for_edit: str = "maintainer"
    roles: dict[str, list[str]] = field(default_factory=dict)
    notify_slack_webhook: str = ""
    notify_teams_webhook: str = ""
    max_diff_tokens: int = 12000
    inline_comments: bool = True
    auto_review: bool = True
    auto_describe: bool = True
    auto_label: bool = True
    auto_security: bool = True

    def is_tool_allowed(self, tool: str) -> bool:
        return tool in self.allowed_tools or "*" in self.allowed_tools

    def can_user_edit(self, username: str) -> bool:
        if not self.allow_edit:
            return False
        required = self.required_role_for_edit
        return username in self.roles.get(required, [])

    def get_user_role(self, username: str) -> str:
        for role, users in self.roles.items():
            if username in users:
                return role
        return "viewer"


class PolicyEngine:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self._global: dict[str, Any] = {}
        self._cache: dict[str, RepoPolicy] = {}
        self._load_global()

    def _load_global(self):
        policy_file = self.config.get("policy_file", settings.policy_file)
        path = Path(policy_file)
        if path.exists():
            with open(path) as f:
                self._global = yaml.safe_load(f) or {}
            logger.info(f"[Policy] Loaded global policy from {path}")
        else:
            logger.warning(f"[Policy] No policy file at {path}, using defaults")

    def reload(self):
        """Hot-reload policy without restart."""
        self._cache.clear()
        self._load_global()
        logger.info("[Policy] Reloaded")

    def get_policy(self, repo_full_name: str, per_repo_cfg: dict | None = None) -> RepoPolicy:
        cache_key = f"{repo_full_name}:{hash(str(per_repo_cfg))}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Start with global defaults
        base = dict(self._global.get("defaults", {}))

        # Match repo patterns (supports wildcards like 'org/*')
        for pattern, rule in self._global.get("repos", {}).items():
            if self._matches(repo_full_name, pattern):
                base = {**base, **rule}
                break

        # Per-repo config wins over everything
        merged = {**base, **(per_repo_cfg or {})}
        policy = self._build(merged)
        self._cache[cache_key] = policy
        return policy

    def apply(self, result: Any) -> Any:
        """Apply policy rules to a ReviewResult."""
        policy = self.get_policy(result.repo)
        
        # Enforce minimum score for approval
        if result.score < policy.min_score_to_approve:
            result.approved = False
            
        # Filter comments for excluded files
        if policy.excluded_files:
            filtered_comments = []
            for comment in result.comments:
                excluded = False
                for pattern in policy.excluded_files:
                    if re.search(pattern, comment.path):
                        excluded = True
                        break
                if not excluded:
                    filtered_comments.append(comment)
            result.comments = filtered_comments
            
        # Example: if critical security issue found, force not approved
        has_critical_security = any(
            c.severity == "critical" and c.category == "security" 
            for c in result.comments
        )
        if has_critical_security:
            result.approved = False
            
        return result

    def _matches(self, repo: str, pattern: str) -> bool:
        if pattern.endswith("/*"):
            return repo.startswith(pattern[:-1])
        return repo == pattern

    def _build(self, cfg: dict) -> RepoPolicy:
        return RepoPolicy(
            allowed_tools=cfg.get("allowed_tools", settings.default_allowed_tools),
            allowed_llm_providers=cfg.get("allowed_llm_providers", [settings.llm_provider]),
            allowed_llm_models=cfg.get("allowed_llm_models", []),
            allow_edit=cfg.get("allow_edit", False),
            allow_auto_merge=cfg.get("allow_auto_merge", False),
            required_role_for_edit=cfg.get("required_role_for_edit", "maintainer"),
            roles=cfg.get("roles", {}),
            notify_slack_webhook=cfg.get("notify_slack_webhook", settings.slack_webhook_url),
            notify_teams_webhook=cfg.get("notify_teams_webhook", settings.teams_webhook_url),
            max_diff_tokens=cfg.get("max_diff_tokens", settings.max_diff_tokens),
            inline_comments=cfg.get("inline_comments", settings.inline_comments),
            auto_review=cfg.get("auto_review", settings.auto_review_on_open),
            auto_describe=cfg.get("auto_describe", settings.auto_describe_on_open),
            auto_label=cfg.get("auto_label", settings.auto_label_on_open),
            auto_security=cfg.get("auto_security", settings.auto_security_on_open),
        )

    def update_policy(self, repo_full_name: str, updates: dict) -> bool:
        """Update policy for a specific repo (used by UI dashboard)."""
        path = Path(settings.policy_file)
        data = self._global
        if "repos" not in data:
            data["repos"] = {}
        data["repos"][repo_full_name] = {
            **data["repos"].get(repo_full_name, {}),
            **updates
        }
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)
        self._global = data
        self._cache.clear()
        logger.info(f"[Policy] Updated policy for {repo_full_name}")
        return True

    def get_all_policies(self) -> dict:
        """Return all policies for UI display."""
        return {
            "defaults": self._global.get("defaults", {}),
            "repos": self._global.get("repos", {}),
        }


policy_engine = PolicyEngine()
