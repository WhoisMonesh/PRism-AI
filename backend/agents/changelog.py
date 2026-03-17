from ..llm_backends import get_llm_client


class ChangelogAgent:
    def __init__(self):
        self.llm = get_llm_client()

    async def run(self, diff: str, files: list[dict]) -> str:
        prompt = self._build_prompt(diff, files)
        response = await self.llm.generate(prompt, temperature=0.3)
        return response

    def _build_prompt(self, diff: str, files: list[dict]) -> str:
        file_list = "\n".join(f"- {f.get('filename', 'unknown')}" for f in files[:20])

        return f"""You are a technical writer generating changelog entries.

Analyze this Pull Request and create a changelog entry.

Files changed:
{file_list}

Diff:
```
{diff[:6000]}
```

Generate a changelog entry in this format:

### [Type] Brief Title

**Added:**
- Feature or capability additions

**Changed:**
- Modifications to existing functionality

**Fixed:**
- Bug fixes

**Removed:**
- Deprecated or removed features

**Security:**
- Security improvements

Types: Feature, Bugfix, Enhancement, Refactor, Documentation, Security

Keep entries user-facing and avoid internal implementation details."""
