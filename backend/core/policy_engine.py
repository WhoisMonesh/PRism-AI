import yaml
import re
from pathlib import Path
from typing import Optional
from ..models import PolicyRule
from ..config import get_settings


class PolicyEngine:
    def __init__(self):
        self.settings = get_settings()
        self.policies: list[PolicyRule] = []
        self.load_policies()

    def load_policies(self):
        policy_file = Path(self.settings.policy_file)
        if not policy_file.exists():
            self.policies = [self._default_policy()]
            return

        try:
            with open(policy_file, 'r') as f:
                data = yaml.safe_load(f)
                self.policies = [PolicyRule(**rule) for rule in data.get("policies", [])]
        except Exception as e:
            print(f"Failed to load policy file: {e}")
            self.policies = [self._default_policy()]

    def get_policy(self, repo_full_name: str) -> PolicyRule:
        for policy in self.policies:
            if self._match_pattern(policy.repo_pattern, repo_full_name):
                return policy
        return self._default_policy()

    def is_tool_allowed(self, repo_full_name: str, tool: str) -> bool:
        policy = self.get_policy(repo_full_name)
        return tool in policy.allowed_tools

    def is_edit_allowed(self, repo_full_name: str) -> bool:
        policy = self.get_policy(repo_full_name)
        return policy.allow_edit

    def get_min_score(self, repo_full_name: str) -> int:
        policy = self.get_policy(repo_full_name)
        return policy.min_score

    def is_file_blocked(self, repo_full_name: str, file_path: str) -> bool:
        policy = self.get_policy(repo_full_name)
        for pattern in policy.blocked_patterns:
            if self._match_pattern(pattern, file_path):
                return True
        return False

    def filter_files(self, repo_full_name: str, files: list[dict]) -> list[dict]:
        policy = self.get_policy(repo_full_name)
        if not policy.blocked_patterns:
            return files

        filtered = []
        for file in files:
            file_path = file.get("filename", "")
            if not self.is_file_blocked(repo_full_name, file_path):
                filtered.append(file)
        return filtered

    def _match_pattern(self, pattern: str, text: str) -> bool:
        pattern = pattern.replace("*", ".*").replace("?", ".")
        return bool(re.fullmatch(pattern, text))

    def _default_policy(self) -> PolicyRule:
        return PolicyRule(
            repo_pattern="*",
            allowed_tools=["review", "describe", "improve", "security", "changelog",
                          "ask", "labels", "test_gen", "perf", "self_review", "auto_issue"],
            allowed_llms=[{"provider": "ollama", "models": ["llama3.1", "llama2:latest"]}],
            allow_edit=False,
            min_score=70,
            blocked_patterns=[],
            severity_overrides={}
        )
