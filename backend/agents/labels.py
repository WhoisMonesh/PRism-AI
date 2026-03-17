from ..llm_backends import get_llm_client
import json
import re


class LabelsAgent:
    def __init__(self):
        self.llm = get_llm_client()

    async def run(self, diff: str, files: list[dict]) -> list[str]:
        prompt = self._build_prompt(diff, files)
        response = await self.llm.generate(prompt, temperature=0.2)
        return self._parse_response(response)

    def _build_prompt(self, diff: str, files: list[dict]) -> str:
        file_list = "\n".join(f"- {f.get('filename', 'unknown')}" for f in files[:20])

        return f"""Analyze this Pull Request and suggest appropriate labels.

Files changed:
{file_list}

Diff:
```
{diff[:6000]}
```

Return a JSON array of label strings:
["label1", "label2", ...]

Common labels:
- bug, feature, enhancement, refactor, documentation
- breaking-change, dependencies, security, performance
- backend, frontend, database, infrastructure
- needs-review, work-in-progress, ready-to-merge
- high-priority, low-priority

Choose 3-6 most relevant labels. Return ONLY valid JSON array."""

    def _parse_response(self, response: str) -> list[str]:
        try:
            json_match = re.search(r'\[.*?\]', response, re.DOTALL)
            if json_match:
                response = json_match.group(0)
            labels = json.loads(response)
            return [str(label) for label in labels if isinstance(label, str)]
        except:
            return ["needs-review", "ai-labeled"]
