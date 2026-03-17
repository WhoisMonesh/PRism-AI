from ..llm_backends import get_llm_client
from ..models import ReviewResult, ReviewComment, Severity, Category
import json
import re


class ReviewAgent:
    def __init__(self):
        self.llm = get_llm_client()

    async def run(self, diff: str, files: list[dict]) -> ReviewResult:
        prompt = self._build_prompt(diff, files)
        response = await self.llm.generate(prompt, temperature=0.2)
        return self._parse_response(response)

    def _build_prompt(self, diff: str, files: list[dict]) -> str:
        file_list = "\n".join(f"- {f.get('filename', 'unknown')}" for f in files[:20])

        return f"""You are a senior code reviewer conducting a thorough Pull Request review.

Analyze this diff and provide a structured review in JSON format.

Files changed:
{file_list}

Diff:
```
{diff[:8000]}
```

Provide your review as a JSON object with this exact structure:
{{
  "score": <integer 0-100>,
  "approved": <boolean>,
  "summary": "<brief overall assessment>",
  "comments": [
    {{
      "path": "<file path>",
      "line": <line number or null>,
      "severity": "<critical|warning|info|suggestion>",
      "category": "<bug|security|performance|maintainability|style|documentation|test|general>",
      "message": "<detailed explanation>",
      "suggestion": "<optional code suggestion or null>"
    }}
  ]
}}

Focus on:
- Bugs and logical errors (critical)
- Security vulnerabilities (critical)
- Performance issues (warning)
- Code quality and maintainability (warning/info)
- Best practices and style (suggestion)

Return ONLY valid JSON, no markdown formatting."""

    def _parse_response(self, response: str) -> ReviewResult:
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                response = json_match.group(0)

            data = json.loads(response)

            comments = []
            for c in data.get("comments", []):
                # Safe severity parsing
                try:
                    severity = Severity(c.get("severity", "info"))
                except ValueError:
                    severity = Severity.INFO
                
                # Safe category parsing
                try:
                    category = Category(c.get("category", "general"))
                except ValueError:
                    category = Category.GENERAL

                comments.append(ReviewComment(
                    path=c["path"],
                    line=c.get("line"),
                    severity=severity,
                    category=category,
                    message=c["message"],
                    suggestion=c.get("suggestion")
                ))

            return ReviewResult(
                score=data["score"],
                approved=data["approved"],
                summary=data["summary"],
                comments=comments
            )
        except Exception as e:
            return ReviewResult(
                score=50,
                approved=False,
                summary=f"Failed to parse AI response: {e}\n\nRaw response:\n{response[:500]}",
                comments=[]
            )
