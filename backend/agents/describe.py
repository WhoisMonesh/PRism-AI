from ..llm_backends import get_llm_client


class DescribeAgent:
    def __init__(self):
        self.llm = get_llm_client()

    async def run(self, diff: str, files: list[dict]) -> str:
        prompt = self._build_prompt(diff, files)
        response = await self.llm.generate(prompt, temperature=0.3)
        return response

    def _build_prompt(self, diff: str, files: list[dict]) -> str:
        file_list = "\n".join(f"- {f.get('filename', 'unknown')}" for f in files[:20])

        return f"""You are assisting with Pull Request documentation.

Summarize this Pull Request in a clear, concise way for human reviewers.

Files changed:
{file_list}

Diff:
```
{diff[:6000]}
```

Provide:
1. **Summary**: One sentence overview
2. **Changes**: Bullet list of key changes (max 10 points)
3. **Impact**: What parts of the system are affected
4. **Risk Level**: Low/Medium/High with brief justification

Keep it under 300 words."""
