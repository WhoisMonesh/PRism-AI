from ..llm_backends import get_llm_client


class SelfReviewAgent:
    def __init__(self):
        self.llm = get_llm_client()

    async def run(self, diff: str, files: list[dict]) -> str:
        prompt = self._build_prompt(diff, files)
        response = await self.llm.generate(prompt, temperature=0.3)
        return response

    def _build_prompt(self, diff: str, files: list[dict]) -> str:
        file_list = "\n".join(f"- {f.get('filename', 'unknown')}" for f in files[:20])

        return f"""You are helping a developer prepare their PR for review.

Create a self-review checklist and preparation guide.

Files changed:
{file_list}

Diff:
```
{diff[:8000]}
```

Provide:

**Pre-Review Checklist:**
- [ ] Items to verify before requesting review

**Testing Recommendations:**
- What should be tested manually
- Automated tests to add

**Documentation Updates:**
- README changes needed
- API documentation updates
- Code comments to add

**Reviewer Guidance:**
- Key areas for reviewers to focus on
- Context reviewers should know
- Trade-offs made

**Known Issues:**
- Technical debt introduced
- Follow-up tasks

Make this actionable and specific to the changes."""
