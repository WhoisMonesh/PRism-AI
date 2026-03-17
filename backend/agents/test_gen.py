from ..llm_backends import get_llm_client


class TestGenAgent:
    def __init__(self):
        self.llm = get_llm_client()

    async def run(self, diff: str, files: list[dict]) -> str:
        prompt = self._build_prompt(diff, files)
        response = await self.llm.generate(prompt, temperature=0.3)
        return response

    def _build_prompt(self, diff: str, files: list[dict]) -> str:
        file_list = "\n".join(f"- {f.get('filename', 'unknown')}" for f in files[:20])

        return f"""You are a test automation expert.

Generate comprehensive test cases for this Pull Request.

Files changed:
{file_list}

Diff:
```
{diff[:8000]}
```

For each changed file/function, provide:

1. **Unit Tests**: Test individual functions/methods
2. **Integration Tests**: Test component interactions
3. **Edge Cases**: Boundary conditions, error handling
4. **Test Data**: Sample inputs and expected outputs

Format as code blocks in the appropriate testing framework (Jest, pytest, JUnit, etc. based on the language).

Include:
- Test descriptions
- Setup/teardown if needed
- Assertions
- Mock/stub suggestions"""
