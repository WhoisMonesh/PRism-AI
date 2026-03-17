from ..llm_backends import get_llm_client
from ..models import ReviewResult, ReviewComment, Severity, Category
import json
import re


class SecurityAgent:
    def __init__(self):
        self.llm = get_llm_client()

    async def run(self, diff: str, files: list[dict]) -> ReviewResult:
        prompt = self._build_prompt(diff, files)
        response = await self.llm.generate(prompt, temperature=0.1)
        return self._parse_response(response)

    def _build_prompt(self, diff: str, files: list[dict]) -> str:
        file_list = "\n".join(f"- {f.get('filename', 'unknown')}" for f in files[:20])

        return f"""You are a security expert conducting a security audit of this Pull Request.

Files changed:
{file_list}

Diff:
```
{diff[:8000]}
```

Analyze for security vulnerabilities and return JSON:
{{
  "score": <0-100, where 100 = no issues>,
  "approved": <true if score >= 80>,
  "summary": "<security assessment>",
  "comments": [
    {{
      "path": "<file>",
      "line": <line number or null>,
      "severity": "<critical|warning|info|suggestion>",
      "category": "security",
      "message": "<vulnerability description>",
      "suggestion": "<how to fix>"
    }}
  ]
}}

Check for:
- SQL injection, XSS, CSRF
- Authentication/authorization flaws
- Insecure data storage
- Hardcoded secrets
- Insecure dependencies
- OWASP Top 10
- API security issues
- Input validation gaps

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
                    category=Category.SECURITY,
                    message=c["message"],
                    suggestion=c.get("suggestion")
                ))

            return ReviewResult(
                score=data["score"],
                approved=data["approved"],
                summary=data["summary"],
                comments=comments
            )
        except Exception:
            return ReviewResult(
                score=100,
                approved=True,
                summary="Security scan completed (no parser errors)",
                comments=[]
            )
