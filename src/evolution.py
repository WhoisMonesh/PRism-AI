"""
PRism-AI Evolution Engine
- Learns from reviewer feedback (thumbs up/down on comments)
- Auto-improves prompts based on accepted vs rejected suggestions
- Tracks metrics: review quality, false positive rate, response time
- Self-reviews its own repo (PRism-AI) on a schedule
- Zero hardcoded behaviour - everything adapts over time
"""
from __future__ import annotations
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from .config import settings


METRICS_FILE = Path("data/evolution_metrics.json")
PROMPT_STORE = Path("data/evolved_prompts.json")


class EvolutionMetrics:
    """Tracks per-tool quality metrics to drive prompt evolution."""

    def __init__(self):
        METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict[str, Any] = self._load()

    def _load(self) -> dict:
        if METRICS_FILE.exists():
            return json.loads(METRICS_FILE.read_text())
        return {"tools": {}, "reviews": [], "last_evolved": None}

    def _save(self):
        METRICS_FILE.write_text(json.dumps(self._data, indent=2, default=str))

    def record_review(self, tool: str, pr_url: str, model: str, tokens_used: int,
                      latency_ms: float, feedback: str | None = None):
        """Record a completed review event."""
        entry = {
            "ts": datetime.utcnow().isoformat(),
            "tool": tool,
            "pr_url": pr_url,
            "model": model,
            "tokens_used": tokens_used,
            "latency_ms": latency_ms,
            "feedback": feedback,  # 'positive' | 'negative' | None
        }
        self._data["reviews"].append(entry)
        # trim old data beyond retention window
        cutoff = datetime.utcnow() - timedelta(days=settings.evolution_metrics_retention_days)
        self._data["reviews"] = [
            r for r in self._data["reviews"]
            if datetime.fromisoformat(r["ts"]) > cutoff
        ]
        self._save()
        logger.debug(f"[Evolution] Recorded review metric for tool={tool}")

    def record_feedback(self, pr_url: str, tool: str, is_positive: bool):
        """Update existing review record with human feedback."""
        for r in reversed(self._data["reviews"]):
            if r["pr_url"] == pr_url and r["tool"] == tool:
                r["feedback"] = "positive" if is_positive else "negative"
                self._save()
                logger.info(f"[Evolution] Feedback recorded: tool={tool} positive={is_positive}")
                return

    def get_tool_stats(self, tool: str) -> dict:
        """Return acceptance rate and average latency for a tool."""
        entries = [r for r in self._data["reviews"] if r["tool"] == tool]
        if not entries:
            return {"count": 0, "positive_rate": 0.0, "avg_latency_ms": 0.0}
        with_feedback = [e for e in entries if e["feedback"]]
        positive = sum(1 for e in with_feedback if e["feedback"] == "positive")
        rate = positive / len(with_feedback) if with_feedback else 0.0
        avg_lat = sum(e["latency_ms"] for e in entries) / len(entries)
        return {"count": len(entries), "positive_rate": rate, "avg_latency_ms": avg_lat}

    def summary(self) -> dict:
        tools = set(r["tool"] for r in self._data["reviews"])
        return {t: self.get_tool_stats(t) for t in tools}


class PromptEvolver:
    """Auto-improves prompts based on acceptance metrics."""

    BASE_PROMPTS: dict[str, str] = {
        "review": (
            "You are an expert senior software engineer performing a thorough code review.\n"
            "Analyse the diff carefully. For each issue found:\n"
            "- State the file and line number\n"
            "- Classify severity: CRITICAL / HIGH / MEDIUM / LOW / INFO\n"
            "- Explain the issue clearly\n"
            "- Suggest a concrete fix\n"
            "Format as markdown. Be direct. Do not praise the code unnecessarily.\n"
        ),
        "describe": (
            "You are a technical writer summarising a pull request for reviewers.\n"
            "Provide:\n"
            "1. One-line summary (under 80 chars)\n"
            "2. What changed and why (3-7 bullet points)\n"
            "3. Type of change: feature / bugfix / refactor / docs / test / chore\n"
            "4. Risk level: low / medium / high\n"
        ),
        "improve": (
            "You are an expert software engineer suggesting concrete code improvements.\n"
            "For each improvement:\n"
            "- Show the original code snippet\n"
            "- Show the improved version\n"
            "- Explain why it is better\n"
            "Focus on: correctness, performance, readability, security, maintainability.\n"
        ),
        "security": (
            "You are a security engineer performing a security audit of this code diff.\n"
            "Check for: SQL injection, XSS, SSRF, hardcoded secrets, insecure deserialization,\n"
            "broken auth, path traversal, command injection, insecure dependencies.\n"
            "Rate each finding: CRITICAL / HIGH / MEDIUM / LOW\n"
            "Provide OWASP category and a concrete remediation for each.\n"
        ),
        "test_gen": (
            "You are a senior test engineer. Generate comprehensive unit tests for the changed code.\n"
            "Use the same language and test framework as the existing codebase.\n"
            "Cover: happy path, edge cases, error conditions, boundary values.\n"
            "Return only valid, runnable test code.\n"
        ),
        "changelog": (
            "You are a technical writer generating a changelog entry for this pull request.\n"
            "Format: Keep-a-Changelog (https://keepachangelog.com).\n"
            "Categorise under: Added / Changed / Deprecated / Removed / Fixed / Security.\n"
        ),
        "performance": (
            "You are a performance engineering expert reviewing this code diff.\n"
            "Identify: N+1 queries, O(n^2) algorithms, memory leaks, blocking I/O,\n"
            "unnecessary allocations, missing caching opportunities.\n"
            "Quantify impact where possible and suggest specific optimisations.\n"
        ),
        "self_review": (
            "You are reviewing your own source code (PRism-AI) to find improvements.\n"
            "Focus on: code quality, missing error handling, hardcoded values, test coverage gaps,\n"
            "prompt quality improvements, new features that would be useful.\n"
            "Create actionable GitHub issues from your findings.\n"
        ),
    }

    def __init__(self, metrics: EvolutionMetrics):
        self._metrics = metrics
        PROMPT_STORE.parent.mkdir(parents=True, exist_ok=True)
        self._evolved: dict[str, str] = self._load()

    def _load(self) -> dict:
        if PROMPT_STORE.exists():
            return json.loads(PROMPT_STORE.read_text())
        return {}

    def _save(self):
        PROMPT_STORE.write_text(json.dumps(self._evolved, indent=2))

    def get_prompt(self, tool: str) -> str:
        """Return evolved prompt if available, else base prompt."""
        return self._evolved.get(tool, self.BASE_PROMPTS.get(tool, ""))

    async def evolve_prompt(self, tool: str, llm_client: Any):
        """Ask LLM to improve the current prompt based on metrics."""
        if not settings.evolution_auto_improve_prompts:
            return
        stats = self._metrics.get_tool_stats(tool)
        if stats["count"] < 10:  # not enough data yet
            return
        current_prompt = self.get_prompt(tool)
        meta_prompt = (
            f"You are a prompt engineer. The following prompt is used by PRism-AI for the '{tool}' agent.\n"
            f"Current acceptance rate: {stats['positive_rate']:.0%} over {stats['count']} reviews.\n"
            f"Improve the prompt to make reviews more accurate, specific, and useful.\n"
            f"Return ONLY the improved prompt text, nothing else.\n\n"
            f"CURRENT PROMPT:\n{current_prompt}"
        )
        try:
            improved = await llm_client.generate(meta_prompt)
            if improved and len(improved) > 100:
                self._evolved[tool] = improved.strip()
                self._save()
                logger.info(f"[Evolution] Prompt evolved for tool={tool}")
        except Exception as e:
            logger.warning(f"[Evolution] Prompt evolution failed for {tool}: {e}")


class SelfReviewer:
    """PRism-AI reviews its own GitHub repository on a schedule."""

    async def run(self):
        """Trigger a full review of the PRism-AI repo's latest commits."""
        if not settings.self_review_enabled:
            logger.info("[SelfReview] Disabled via config")
            return
        logger.info(
            f"[SelfReview] Starting self-review of "
            f"{settings.self_repo_owner}/{settings.self_repo_name}"
        )
        try:
            from .git_providers.github_provider import GitHubProvider
            from .agents.self_review import SelfReviewAgent
            from .llm_backends import get_llm_client

            provider = GitHubProvider(
                owner=settings.self_repo_owner,
                repo=settings.self_repo_name,
            )
            diff = await provider.get_branch_diff(
                base="HEAD~5",
                head=settings.self_review_branch,
            )
            llm = get_llm_client()
            agent = SelfReviewAgent(provider=provider, llm=llm)
            issues = await agent.run(diff=diff)
            if issues:
                for issue in issues:
                    await provider.create_issue(
                        title=issue["title"],
                        body=issue["body"],
                        labels=["self-review", "enhancement"],
                    )
                logger.info(f"[SelfReview] Created {len(issues)} improvement issues")
            else:
                logger.info("[SelfReview] No improvements found in this cycle")
        except Exception as e:
            logger.error(f"[SelfReview] Failed: {e}")


class EvolutionEngine:
    """Orchestrates all evolution activities with scheduled jobs."""

    def __init__(self):
        self.metrics = EvolutionMetrics()
        self.prompt_evolver = PromptEvolver(self.metrics)
        self.self_reviewer = SelfReviewer()
        self._scheduler = AsyncIOScheduler()

    def start(self):
        if not settings.evolution_enabled:
            logger.info("[Evolution] Engine disabled")
            return

        # Self-review on cron schedule (default: 2am daily)
        self._scheduler.add_job(
            self.self_reviewer.run,
            CronTrigger.from_crontab(settings.self_review_schedule),
            id="self_review",
            replace_existing=True,
        )

        # Evolve prompts weekly
        self._scheduler.add_job(
            self._evolve_all_prompts,
            CronTrigger.from_crontab("0 3 * * 0"),  # Sunday 3am
            id="prompt_evolution",
            replace_existing=True,
        )

        self._scheduler.start()
        logger.info("[Evolution] Engine started - self-review & prompt evolution scheduled")

    def stop(self):
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    async def _evolve_all_prompts(self):
        from .llm_backends import get_llm_client
        llm = get_llm_client()
        for tool in PromptEvolver.BASE_PROMPTS:
            await self.prompt_evolver.evolve_prompt(tool, llm)
            await asyncio.sleep(2)  # rate limit

    def record_review(self, **kwargs):
        self.metrics.record_review(**kwargs)

    def record_feedback(self, pr_url: str, tool: str, is_positive: bool):
        self.metrics.record_feedback(pr_url=pr_url, tool=tool, is_positive=is_positive)

    def get_prompt(self, tool: str) -> str:
        return self.prompt_evolver.get_prompt(tool)

    def get_summary(self) -> dict:
        return self.metrics.summary()


# Singleton
evolution_engine = EvolutionEngine()
