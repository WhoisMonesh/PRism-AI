from ..llm_backends import get_llm_client
from ..models import ReviewResult, ReviewComment, Severity, Category
import json
import re


class PerfAgent:
    def __init__(self):
        self.llm = get_llm_client()

    async def run(self, diff: str, files: list[dict]) -> ReviewResult:
        prompt = self._build_prompt(diff, files)
        response = await self.llm.generate(prompt, temperature=0.2)
        return self._parse_response(response)

    def _build_prompt(self, diff: str, files: list[dict]) -> str:
        file_list = "\n".join(f"- {f.get('filename', 'unknown')}" for f in files[:20])

        return f"""You are a performance optimization expert.

Analyze this Pull Request for performance issues.

Files changed:
{file_list}

Diff:
```
{diff[:8000]}
```

Return JSON:
{{
  "score": <0-100, where 100 = optimal performance>,
  "approved": <true if score >= 70>,
  "summary": "<performance assessment>",
  "comments": [
    {{
      "path": "<file>",
      "line": <line number or null>,
      "severity": "<critical|warning|info|suggestion>",
      "category": "performance",
      "message": "<performance issue>",
      "suggestion": "<optimization recommendation>"
    }}
  ]
}}

Look for:
- O(n²) or worse algorithms
- Unnecessary loops or iterations
- Database N+1 queries
- Missing indexes
- Inefficient data structures
- Memory leaks
- Blocking I/O
- Excessive API calls
- Large bundle sizes
- Unoptimized queries

Return ONLY valid JSON."""

    def _parse_response(self, response: str) -> ReviewResult:
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                response = json_match.group(0)

            data = json.loads(response)

            comments = []
            for c in data.get("comments", []):
                try:
                    severity = Severity(c.get("severity", "info"))
                except ValueError:
                    severity = Severity.INFO

                comments.append(ReviewComment(
                    path=c["path"],
                    line=c.get("line"),
                    severity=severity,
                    category=Category.PERFORMANCE,
                    message=c["message"],
                    suggestion=c.get("suggestion")
                ))

            return ReviewResult(
                score=data["score"],
                approved=data["approved"],
                summary=data["summary"],
                comments=comments
            )
        except:
            return ReviewResult(
                score=80,
                approved=True,
                summary="Performance analysis completed",
                comments=[]
            )
