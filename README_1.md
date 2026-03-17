# PRism AI

**Free and Open-Source AI-Powered Pull Request Review Agent**

PRism AI is a self-hosted, enterprise-ready PR review automation platform that works with local LLMs (Ollama), cloud AI services (Vertex AI, AWS Bedrock, OpenAI), and supports multiple Git providers with comprehensive RBAC and security controls.

## Features

### Multi-LLM Backend Support
- **Ollama (Local)** - Run completely offline with local models
- **Ollama Cloud** - Cloud-hosted Ollama instances
- **Google Vertex AI** - Gemini models with IAM/Workload Identity
- **AWS Bedrock** - Claude, Titan models with IAM roles
- **OpenAI** - GPT-4 and compatible endpoints (vLLM, LM Studio)

### Multi-Git Provider Support
- GitHub (Enterprise & Cloud)
- GitLab (Self-hosted & Cloud)
- Gitea
- Bitbucket

### Comprehensive AI Tools
- **Review** - Full code review with scoring (0-100)
- **Security** - OWASP Top 10 vulnerability scanning
- **Performance** - Performance bottleneck detection
- **Describe** - PR summary generation
- **Improve** - Refactoring suggestions
- **Changelog** - Auto-generate changelog entries
- **Ask** - Q&A about PR changes
- **Labels** - Automatic PR labeling
- **Test Gen** - Test case generation
- **Self Review** - Developer checklist generator

### Enterprise Security
- Row-level policy engine with repo pattern matching
- Blocked file patterns (vendor, node_modules, etc.)
- Tool and model restrictions per repo
- Min approval score thresholds
- Webhook signature verification (HMAC-SHA256)
- No hardcoded secrets - all via env vars or secret managers

### Prompt Evolution
- Records feedback on AI reviews
- Tracks score improvements over time
- Self-improving prompts based on human feedback

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Git provider account (GitHub, GitLab, etc.)
- LLM backend (Ollama recommended for local setup)

### 1. Clone & Configure

```bash
git clone https://github.com/WhoisMonesh/PRism-AI.git
cd PRism-AI
cp .env.example .env
```

Edit `.env` and configure at minimum:
```bash
GITHUB_TOKEN=ghp_your_token_here
GITHUB_WEBHOOK_SECRET=your_secret_here
LLM_PROVIDER=ollama
```

### 2. Start Services

```bash
docker-compose up -d
```

This starts:
- **PRism AI Backend** - http://localhost:8000
- **Ollama** - http://localhost:11434
- **Frontend UI** - http://localhost:5173

### 3. Pull Ollama Model

```bash
docker exec -it ollama ollama pull llama3.1
```

### 4. Configure Webhooks

#### GitHub
1. Go to repo Settings → Webhooks → Add webhook
2. Payload URL: `http://your-server:8000/api/v1/webhook/github`
3. Content type: `application/json`
4. Secret: (same as `GITHUB_WEBHOOK_SECRET` in `.env`)
5. Events: "Pull requests"

#### GitLab
1. Go to repo Settings → Webhooks
2. URL: `http://your-server:8000/api/v1/webhook/gitlab`
3. Secret token: (same as `GITLAB_WEBHOOK_SECRET`)
4. Trigger: "Merge request events"

### 5. Test Manual Review

Open http://localhost:5173, go to **Review** tab, and submit a PR for review.

## Architecture

```
┌─────────────────┐
│   Developer     │
│   Opens PR      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐       ┌──────────────┐
│  Git Provider   │──────▶│  Webhook     │
│ (GitHub/GitLab) │       │  Handler     │
└─────────────────┘       └──────┬───────┘
                                 │
                                 ▼
                        ┌────────────────┐
                        │ Review Engine  │
                        │  + Policy      │
                        └────┬───────────┘
                             │
                 ┌───────────┼───────────┐
                 ▼           ▼           ▼
         ┌──────────┐  ┌─────────┐  ┌─────────┐
         │  Ollama  │  │ Vertex  │  │Bedrock  │
         │  Local   │  │   AI    │  │ Claude  │
         └──────────┘  └─────────┘  └─────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │  Post Review   │
                    │  Comments +    │
                    │  Inline Notes  │
                    └────────────────┘
```

## Configuration

### Environment Variables

See `.env.example` for all available options. Key settings:

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | Which LLM backend to use | `ollama` |
| `AUTO_REVIEW_ON_PR` | Auto-review on webhook events | `false` |
| `MIN_APPROVAL_SCORE` | Threshold for approval | `70` |
| `POLICY_FILE` | Path to policy YAML | `policy.yaml` |

### Policy Configuration

Edit `policy.yaml` to define per-repo rules:

```yaml
policies:
  - repo_pattern: "myorg/critical-*"
    allowed_tools: ["review", "security"]
    allowed_llms:
      - provider: vertex
        models: ["gemini-1.5-pro"]
    allow_edit: false
    min_score: 90
    blocked_patterns:
      - "*.lock"
      - "dist/*"
    severity_overrides:
      security: critical
```

**Pattern matching**: Use `*` for wildcards (e.g., `*/internal-*` matches `myorg/internal-tools`).

## API Reference

### Manual Review
```bash
POST /api/v1/review
Content-Type: application/json

{
  "pr": {
    "provider": "github",
    "owner": "facebook",
    "repo": "react",
    "number": 12345
  },
  "tool": "review"
}
```

**Available tools**: `review`, `describe`, `improve`, `security`, `changelog`, `ask`, `labels`, `test_gen`, `perf`, `self_review`

### Health Check
```bash
GET /api/v1/health
```

Returns:
```json
{
  "status": "healthy",
  "llm_backend": "ollama",
  "llm_available": true,
  "git_providers": {
    "github": true,
    "gitlab": false
  }
}
```

### Settings
```bash
GET /api/v1/settings
POST /api/v1/settings
```

### Submit Feedback
```bash
POST /api/v1/feedback
{
  "prompt_id": "abc123",
  "tool": "review",
  "was_helpful": true,
  "score_before": 65,
  "score_after": 85
}
```

## LLM Backend Setup

### Ollama (Local)
```bash
docker exec -it ollama ollama pull llama3.1
docker exec -it ollama ollama pull qwen2.5-coder
```

Set in `.env`:
```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.1
```

### Vertex AI (Google Cloud)
1. Create service account with Vertex AI User role
2. Download JSON key to `/secrets/gcp-sa.json`
3. Set in `.env`:
```bash
LLM_PROVIDER=vertex
VERTEX_PROJECT_ID=my-project
VERTEX_LOCATION=us-central1
VERTEX_MODEL=gemini-1.5-pro
VERTEX_CREDENTIALS_PATH=/secrets/gcp-sa.json
```

### AWS Bedrock
Using IAM role (recommended):
```bash
LLM_PROVIDER=bedrock
BEDROCK_REGION=us-east-1
BEDROCK_MODEL=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_ROLE_ARN=arn:aws:iam::123456789012:role/bedrock-reviewer
```

Or with access keys:
```bash
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
```

### OpenAI / Compatible
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
```

For vLLM or LM Studio:
```bash
OPENAI_BASE_URL=http://localhost:8080/v1
```

## Security Best Practices

1. **Never commit secrets** - Use `.env` file (gitignored)
2. **Use IAM roles** instead of API keys where possible (Vertex, Bedrock)
3. **Enable webhook signature verification** - Set strong `WEBHOOK_SECRET`
4. **Restrict by policy** - Use `policy.yaml` to enforce tool/model restrictions
5. **Block sensitive files** - Add to `blocked_patterns` in policy
6. **Run behind firewall** - For intranet deployment, restrict outbound to only LLM endpoints
7. **Use HTTPS** - Always use TLS for webhooks in production

## Deployment

### Docker Compose (Recommended)
```bash
docker-compose up -d
```

### Kubernetes (Helm)
```bash
helm install prism-ai ./helm/prism-ai \
  --set github.token=$GITHUB_TOKEN \
  --set llm.provider=vertex \
  --set vertex.projectId=$GCP_PROJECT
```

### Manual
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend
npm install
npm run dev
```

## GitHub Actions Integration

Add to `.github/workflows/pr-review.yml`:

```yaml
name: PRism AI Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  ai-review:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Review
        run: |
          curl -X POST "${{ secrets.PRISM_AI_URL }}/api/v1/webhook/github" \
            -H "X-Hub-Signature-256: sha256=${{ secrets.WEBHOOK_SECRET }}" \
            -d @$GITHUB_EVENT_PATH
```

## License

**MIT License** - Free for commercial and personal use.

Unlike PR-Agent (AGPL-3.0), PRism AI uses MIT to enable maximum adoption in both open-source and proprietary enterprise environments.

## Comparison to PR-Agent

| Feature | PRism AI | PR-Agent |
|---------|----------|----------|
| License | MIT | AGPL-3.0 |
| Local LLM | ✅ Ollama | ❌ Cloud only |
| Vertex AI | ✅ With IAM | ✅ |
| AWS Bedrock | ✅ With IAM | ❌ |
| Gitea | ✅ | ❌ |
| RBAC Policies | ✅ YAML-based | Limited |
| Prompt Evolution | ✅ Feedback loop | ❌ |
| Self-Hosted UI | ✅ React dashboard | ❌ CLI/Action only |
| Free Tier | ✅ Fully free | Limited |

## Roadmap

- [ ] Supabase integration for review history
- [ ] Multi-language support (UI)
- [ ] Advanced analytics dashboard
- [ ] GPT-based auto-fix suggestions
- [ ] Slack/Teams notifications
- [ ] Fine-tuning support for custom models
- [ ] Browser extension for inline AI chat

## Contributing

PRism AI is fully open-source. Contributions welcome!

1. Fork the repo
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## Support

- GitHub Issues: https://github.com/WhoisMonesh/PRism-AI/issues
- Discussions: https://github.com/WhoisMonesh/PRism-AI/discussions

## Acknowledgments

Inspired by [PR-Agent](https://github.com/Codium-ai/pr-agent) but redesigned for:
- Complete local/offline operation
- Enterprise intranet deployment
- Multi-cloud LLM flexibility
- Permissive licensing (MIT vs AGPL)
