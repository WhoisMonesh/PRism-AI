from ..llm_backends import get_llm_client


class AskAgent:
    def __init__(self):
        self.llm = get_llm_client()

    async def run(self, diff: str, files: list[dict], question: str) -> str:
        prompt = self._build_prompt(diff, files, question)
        response = await self.llm.generate(prompt, temperature=0.4)
        return response

    def _build_prompt(self, diff: str, files: list[dict], question: str) -> str:
        file_list = "\n".join(f"- {f.get('filename', 'unknown')}" for f in files[:20])

        return f"""You are a code expert answering questions about a Pull Request.

Files changed:
{file_list}

Diff:
```
{diff[:8000]}
```

Question: {question}

Provide a clear, technical answer based on the code changes shown. Include:
- Direct answer to the question
- Relevant code references (file:line)
- Examples from the diff if applicable

Be concise but thorough."""
