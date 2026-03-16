"""Core PR review engine for PRism-AI."""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from .llm_backends import get_llm_client as create_llm_client
from .policy import PolicyEngine

logger = logging.getLogger(__name__)


@dataclass
class ReviewComment:
    path: str
    line: Optional[int]
    severity: str  # critical | warning | info | suggestion
    category: str  # security | performance | style | logic | docs
    message: str
    suggestion: Optional[str] = None


@dataclass
class ReviewResult:
    pr_number: int
    repo: str
    summary: str
    score: int  # 0-100
    approved: bool
    comments: List[ReviewComment] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


SYSTEM_PROMPT = """You are PRism-AI, an expert code review assistant.
Your role is to analyze pull request diffs and provide detailed, actionable feedback.
Focus on: security vulnerabilities, logic errors, performance issues, code style,
best practices, and documentation quality.
Always be constructive and specific. Provide line-level comments when possible.
Return your response as valid JSON matching the schema provided."""


class ReviewEngine:
    """Orchestrates LLM-powered code review."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.llm = create_llm_client(config.get("llm", {}))
        self.policy = PolicyEngine(config.get("policy", {}))
        self.max_diff_chars: int = config.get("max_diff_chars", 80_000)

    async def review_pr(
        self,
        pr_number: int,
        repo: str,
        diff: str,
        pr_title: str = "",
        pr_body: str = "",
        changed_files: Optional[List[str]] = None,
    ) -> ReviewResult:
        """Run full AI review of a PR diff."""
        if len(diff) > self.max_diff_chars:
            diff = diff[: self.max_diff_chars] + "\n... [diff truncated] ..."

        prompt = self._build_prompt(pr_number, repo, diff, pr_title, pr_body, changed_files or [])
        logger.info(f"[ReviewEngine] Reviewing PR#{pr_number} in {repo}")

        try:
            raw = await self.llm.generate(prompt, SYSTEM_PROMPT)
            result = self._parse_response(raw, pr_number, repo)
        except Exception as e:
            logger.error(f"[ReviewEngine] LLM error: {e}")
            result = ReviewResult(
                pr_number=pr_number,
                repo=repo,
                summary=f"Review failed: {e}",
                score=0,
                approved=False,
            )

        # Apply policy rules
        result = self.policy.apply(result)
        return result

    def _build_prompt(self, pr_number: int, repo: str, diff: str, title: str, body: str, files: List[str]) -> str:
        files_str = ", ".join(files[:20]) if files else "unknown"
        return f"""Review this pull request:

Repository: {repo}
PR #{pr_number}: {title}
Description: {body or 'No description provided'}
Changed files: {files_str}

Diff:
```
{diff}
```

Provide your review as JSON with this exact structure:
{{
  "summary": "Brief overall summary",
  "score": <0-100 integer quality score>,
  "approved": <true if score >= 70 and no critical issues>,
  "comments": [
    {{
      "path": "file/path.py",
      "line": <line number or null>,
      "severity": "critical|warning|info|suggestion",
      "category": "security|performance|style|logic|docs",
      "message": "Detailed explanation",
      "suggestion": "Code fix suggestion or null"
    }}
  ]
}}"""

    def _parse_response(self, raw: str, pr_number: int, repo: str) -> ReviewResult:
        import json, re
        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', raw)
        if not json_match:
            return ReviewResult(pr_number=pr_number, repo=repo, summary=raw, score=50, approved=False)
        try:
            data = json.loads(json_match.group())
            comments = [
                ReviewComment(
                    path=c.get("path", ""),
                    line=c.get("line"),
                    severity=c.get("severity", "info"),
                    category=c.get("category", "style"),
                    message=c.get("message", ""),
                    suggestion=c.get("suggestion"),
                )
                for c in data.get("comments", [])
            ]
            return ReviewResult(
                pr_number=pr_number,
                repo=repo,
                summary=data.get("summary", ""),
                score=int(data.get("score", 50)),
                approved=bool(data.get("approved", False)),
                comments=comments,
            )
        except Exception as e:
            logger.warning(f"[ReviewEngine] JSON parse error: {e}")
            return ReviewResult(pr_number=pr_number, repo=repo, summary=raw[:500], score=50, approved=False)
