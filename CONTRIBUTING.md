# Contributing to PRism AI

Thank you for considering contributing to PRism AI! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, collaborative, and constructive. We're building this together.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/WhoisMonesh/PRism-AI/issues)
2. If not, create a new issue with:
   - Clear title describing the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Docker version, LLM backend)
   - Relevant logs

### Suggesting Features

1. Check [Discussions](https://github.com/WhoisMonesh/PRism-AI/discussions) for similar ideas
2. Create a new discussion or issue explaining:
   - Use case / problem to solve
   - Proposed solution
   - Alternatives considered

### Pull Requests

1. Fork the repository
2. Create a feature branch from `main`
3. Make your changes
4. Test thoroughly
5. Submit PR with clear description

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose

### Local Development

1. **Clone your fork:**
```bash
git clone https://github.com/YOUR_USERNAME/PRism-AI.git
cd PRism-AI
```

2. **Set up backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

3. **Set up frontend:**
```bash
npm install
```

4. **Run backend:**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

5. **Run frontend:**
```bash
npm run dev
```

6. **Run Ollama (separate terminal):**
```bash
docker run -d -p 11434:11434 --name ollama ollama/ollama
docker exec -it ollama ollama pull llama3.1
```

## Project Structure

```
PRism-AI/
├── backend/
│   ├── main.py              # FastAPI app entry
│   ├── config.py            # Settings & env vars
│   ├── models.py            # Pydantic models
│   ├── agents/              # Review tools
│   │   ├── review.py
│   │   ├── security.py
│   │   └── ...
│   ├── llm_backends/        # LLM integrations
│   │   ├── ollama_backend.py
│   │   ├── vertex_backend.py
│   │   └── ...
│   ├── git_providers/       # Git platform APIs
│   │   ├── github_provider.py
│   │   ├── gitlab_provider.py
│   │   └── ...
│   └── core/
│       ├── policy_engine.py
│       ├── prompt_evolution.py
│       └── review_engine.py
├── src/
│   ├── App.tsx              # Main React app
│   └── components/
│       ├── Dashboard.tsx
│       ├── ReviewPanel.tsx
│       └── SettingsPanel.tsx
├── docker-compose.yml
├── Dockerfile
└── README.md
```

## Coding Standards

### Python

- **Style:** Follow PEP 8
- **Type hints:** Use type annotations for all functions
- **Docstrings:** Add docstrings to public functions
- **Async:** Prefer async/await for I/O operations

Example:
```python
async def get_pr_diff(self, owner: str, repo: str, number: int) -> str:
    """
    Fetch the unified diff for a pull request.

    Args:
        owner: Repository owner
        repo: Repository name
        number: PR number

    Returns:
        Unified diff as string
    """
    # Implementation
```

### TypeScript/React

- **Style:** Functional components with hooks
- **Types:** Use TypeScript interfaces for props
- **Components:** Keep components focused and reusable

Example:
```typescript
interface DashboardProps {
  initialTab?: string;
}

function Dashboard({ initialTab = 'overview' }: DashboardProps) {
  // Component logic
}
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add Bitbucket Cloud support
fix: resolve webhook signature verification issue
docs: update API reference for new endpoints
refactor: simplify ReviewEngine error handling
test: add unit tests for PolicyEngine
```

## Adding New Features

### Adding a New LLM Backend

1. Create `backend/llm_backends/your_backend.py`:
```python
from .base import LLMClient
from ..config import get_settings

class YourBackend(LLMClient):
    def __init__(self):
        settings = get_settings()
        # Initialize your client

    async def generate(self, prompt: str, temperature: float = 0.2, max_tokens: int = 4000) -> str:
        # Implementation

    async def health_check(self) -> bool:
        # Health check

    def get_model_name(self) -> str:
        return "your-model"
```

2. Update `backend/llm_backends/__init__.py`
3. Add to `backend/config.py`
4. Update documentation

### Adding a New Agent Tool

1. Create `backend/agents/your_tool.py`:
```python
from ..llm_backends import get_llm_client

class YourToolAgent:
    def __init__(self):
        self.llm = get_llm_client()

    async def run(self, diff: str, files: list[dict]) -> str:
        prompt = self._build_prompt(diff, files)
        return await self.llm.generate(prompt)

    def _build_prompt(self, diff: str, files: list[dict]) -> str:
        # Build your prompt
        return f"Your prompt template"
```

2. Add to `backend/agents/__init__.py`
3. Update `backend/core/review_engine.py`
4. Add to frontend tool selector

### Adding a New Git Provider

1. Create `backend/git_providers/your_provider.py` implementing `GitProvider` interface
2. Add signature verification
3. Implement all abstract methods
4. Update `backend/git_providers/__init__.py`
5. Add webhook endpoint in `backend/main.py`

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
npm test
```

### Integration Tests
```bash
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## Documentation

- Update README.md for user-facing changes
- Update SETUP.md for deployment changes
- Add inline code comments for complex logic
- Update API docs for new endpoints

## Release Process

1. Update version in `backend/config.py` and `package.json`
2. Update CHANGELOG.md
3. Create release PR
4. Tag release: `git tag v1.x.x`
5. Push tags: `git push --tags`
6. GitHub Actions will build and publish Docker images

## Getting Help

- **Discussions:** https://github.com/WhoisMonesh/PRism-AI/discussions
- **Issues:** https://github.com/WhoisMonesh/PRism-AI/issues

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
