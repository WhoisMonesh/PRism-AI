import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional
from ..models import PromptFeedback


class PromptEvolution:
    def __init__(self, storage_path: str = "data/prompt_evolution.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.feedback_history: list[dict] = []
        self.prompt_versions: dict[str, list[str]] = {}
        self.load_data()

    def load_data(self):
        if not self.storage_path.exists():
            self.feedback_history = []
            self.prompt_versions = {}
            return

        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                self.feedback_history = data.get("feedback", [])
                self.prompt_versions = data.get("versions", {})
        except Exception as e:
            print(f"Failed to load prompt evolution data: {e}")
            self.feedback_history = []
            self.prompt_versions = {}

    def save_data(self):
        try:
            with open(self.storage_path, 'w') as f:
                json.dump({
                    "feedback": self.feedback_history,
                    "versions": self.prompt_versions
                }, f, indent=2)
        except Exception as e:
            print(f"Failed to save prompt evolution data: {e}")

    def record_feedback(self, feedback: PromptFeedback):
        self.feedback_history.append({
            "prompt_id": feedback.prompt_id,
            "tool": feedback.tool,
            "was_helpful": feedback.was_helpful,
            "human_feedback": feedback.human_feedback,
            "score_before": feedback.score_before,
            "score_after": feedback.score_after,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.save_data()

    def get_prompt_id(self, prompt_template: str) -> str:
        return hashlib.sha256(prompt_template.encode()).hexdigest()[:16]

    def register_prompt_version(self, tool: str, prompt_template: str):
        prompt_id = self.get_prompt_id(prompt_template)
        if tool not in self.prompt_versions:
            self.prompt_versions[tool] = []
        if prompt_id not in self.prompt_versions[tool]:
            self.prompt_versions[tool].append(prompt_id)
        self.save_data()
        return prompt_id

    def get_feedback_stats(self, tool: str) -> dict:
        tool_feedback = [f for f in self.feedback_history if f["tool"] == tool]
        if not tool_feedback:
            return {
                "total": 0,
                "helpful": 0,
                "unhelpful": 0,
                "avg_score_before": None,
                "avg_score_after": None,
            }

        helpful = sum(1 for f in tool_feedback if f["was_helpful"])
        scores_before = [f["score_before"] for f in tool_feedback if f["score_before"] is not None]
        scores_after = [f["score_after"] for f in tool_feedback if f["score_after"] is not None]

        return {
            "total": len(tool_feedback),
            "helpful": helpful,
            "unhelpful": len(tool_feedback) - helpful,
            "avg_score_before": sum(scores_before) / len(scores_before) if scores_before else None,
            "avg_score_after": sum(scores_after) / len(scores_after) if scores_after else None,
        }

    def suggest_prompt_improvement(self, tool: str) -> Optional[str]:
        tool_feedback = [f for f in self.feedback_history if f["tool"] == tool]
        if not tool_feedback:
            return None

        recent_negative = [
            f for f in tool_feedback[-20:]
            if not f["was_helpful"] and f.get("human_feedback")
        ]

        if recent_negative:
            suggestions = "\n\n".join(
                f"- {f['human_feedback']}" for f in recent_negative
            )
            return f"Recent negative feedback:\n{suggestions}"

        return None
