from ..llm_backends import get_llm_client


class ImproveAgent:
    def __init__(self):
        self.llm = get_llm_client()

    async def run(self, diff: str, files: list[dict]) -> str:
        prompt = self._build_prompt(diff, files)
        response = await self.llm.generate(prompt, temperature=0.2)
        return response

    def _build_prompt(self, diff: str, files: list[dict]) -> str:
        file_list = "\n".join(f"- {f.get('filename', 'unknown')}" for f in files[:20])

        return f"""You are a code improvement specialist.

Review this PR and suggest specific improvements.

Files changed:
{file_list}

Diff:
```
{diff[:8000]}
```

For each improvement opportunity, provide:
1. **File & Location**: Exact file and line
2. **Issue**: What can be improved
3. **Suggestion**: Specific code improvement
4. **Benefit**: Why this improvement matters

Focus on:
- Refactoring opportunities
- Performance optimizations
- Better error handling
- Improved readability
- Design pattern improvements

Format as markdown with code blocks for suggestions."""
