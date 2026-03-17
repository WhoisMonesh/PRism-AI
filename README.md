# PRism-AI 🔍

> **AI-powered Pull Request Review Bot** for GitHub, GitLab & Gitea — works with **local LLMs** (Ollama), **Vertex AI**, **AWS Bedrock**, and more. Supports **RBAC**, service account credentials, and intranet/air-gapped deployments.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-orange.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)

---

## ✨ Features

- **Multi-platform**: GitHub, GitLab, Gitea (self-hosted or cloud)
- **Multi-LLM**: Ollama (local), OpenAI, Vertex AI (Google Cloud), AWS Bedrock, Azure OpenAI
- **RBAC**: Role-based access control — assign reviewer roles per repo or org
- **Service Account / Credential-based AI access**: Use GCP service accounts, AWS IAM roles, or API keys
- **Intranet / Air-gapped**: Fully deployable behind a firewall with local LLMs
- **Webhook-driven**: Automatically reviews PRs on open/update events
- **Prompt Evolution**: Self-improving prompts based on feedback
- **Policy Engine**: Enforce code standards, security rules, and thresholds
- **Docker & Kubernetes ready**: Helm chart included

---

## 🏗️ Architecture

```
Developer opens / updates a PR
          |
    GitHub / GitLab / Gitea
          | (webhook)
          v
  PRism-AI Backend (FastAPI :8000)
  +------------------------------------------+
  |  WebhookHandler  -->  verify HMAC sig    |
  |  ReviewEngine    -->  build prompt+parse  |
  |  PolicyEngine    -->  RBAC + thresholds   |
  |  PromptEvolution -->  self-improve        |
  |  LLMRouter       -->  pick LLM backend   |
  +------------------------------------------+
          |
    +-----+------+----------+----------+
    |            |          |          |
  Ollama    Vertex AI   Bedrock   OpenAI
 (local)   (GCP SA)   (AWS IAM)  (API key)
```

![PRism-AI Architecture](PRismArch.png)

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/WhoisMonesh/PRism-AI.git
cd PRism-AI
cp .env.example .env
# Edit .env with your settings
```

### 2. Run with Docker Compose

```bash
docker-compose up -d
```

### 3. Run Locally (Dev)

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and configure:

| Variable | Description | Default |
|---|---|---|
| `LLM_PROVIDER` | `ollama`, `openai`, `vertexai`, `bedrock`, `azure` | `ollama` |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Model name for Ollama | `codellama` |
| `OPENAI_API_KEY` | OpenAI API key | — |
| `VERTEXAI_PROJECT` | GCP project ID | — |
| `VERTEXAI_LOCATION` | GCP region | `us-central1` |
| `VERTEXAI_MODEL` | Vertex AI model name | `gemini-1.5-pro` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to GCP service account JSON | — |
| `AWS_REGION` | AWS region for Bedrock | `us-east-1` |
| `BEDROCK_MODEL_ID` | AWS Bedrock model ID | `anthropic.claude-3-sonnet` |
| `AWS_ACCESS_KEY_ID` | AWS access key (or use IAM role) | — |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | — |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | — |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | — |
| `AZURE_OPENAI_DEPLOYMENT` | Azure deployment name | — |
| `GITHUB_TOKEN` | GitHub personal access / app token | — |
| `GITHUB_WEBHOOK_SECRET` | Webhook HMAC secret | — |
| `PRISM_AI_URL` | PRism-AI backend URL (for GitHub Actions workflow) | — |
| `GITLAB_TOKEN` | GitLab private token | — |
| `GITLAB_WEBHOOK_SECRET` | GitLab webhook secret | — |
| `GITEA_TOKEN` | Gitea API token | — |
| `GITEA_BASE_URL` | Gitea instance URL | — |
| `AUTO_REVIEW_ON_OPEN` | Auto-review when PR is opened | `true` |
| `RBAC_ENABLED` | Enable role-based access control | `true` |
| `MAX_FILES_PER_PR` | Max files to review per PR | `50` |
| `MAX_DIFF_LINES` | Max diff lines to send to LLM | `2000` |

---

## 🔐 Authentication & Credential Modes

### Local LLM (Ollama) — No credentials needed
```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=codellama
```

### Google Vertex AI — Service Account
```env
LLM_PROVIDER=vertexai
VERTEXAI_PROJECT=my-gcp-project
VERTEXAI_LOCATION=us-central1
VERTEXAI_MODEL=gemini-1.5-pro
GOOGLE_APPLICATION_CREDENTIALS=/secrets/sa-key.json
```

### AWS Bedrock — IAM Role or Keys
```env
LLM_PROVIDER=bedrock
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
# Leave AWS keys empty to use IAM instance role automatically
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
```

### Azure OpenAI
```env
LLM_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://my-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

---

## 👥 RBAC — Role-Based Access Control

Configure roles in `config/rbac.yaml`:

```yaml
roles:
  admin:
    can_trigger_review: true
    can_approve: true
    can_configure: true
  reviewer:
    can_trigger_review: true
    can_approve: false
    can_configure: false
  viewer:
    can_trigger_review: false
    can_approve: false
    can_configure: false

mappings:
  # GitHub usernames / GitLab usernames / Gitea usernames
  admin:
    - WhoisMonesh
  reviewer:
    - dev-user1
    - dev-user2
  viewer:
    - intern1

# Per-repo overrides
repos:
  WhoisMonesh/PRism-AI:
    reviewer:
      - external-contributor
```

---

## 🪝 Webhook Setup

### GitHub
1. Go to **Repo → Settings → Webhooks → Add webhook**
2. Payload URL: `https://your-server:8000/webhook/github`
3. Content type: `application/json`
4. Secret: value of `GITHUB_WEBHOOK_SECRET`
5. Events: **Pull requests**

### GitLab
1. Go to **Project → Settings → Webhooks**
2. URL: `https://your-server:8000/webhook/gitlab`
3. Secret token: value of `GITLAB_WEBHOOK_SECRET`
4. Trigger: **Merge request events**

### Gitea
1. Go to **Repo → Settings → Webhooks → Add Webhook → Gitea**
2. Target URL: `https://your-server:8000/webhook/gitea`
3. Secret: value of `GITEA_WEBHOOK_SECRET`
4. Trigger: **Pull Request**

---

### GitHub Actions (Alternative Method)

If you prefer to trigger reviews via GitHub Actions instead of webhooks:

1. Copy the workflow file from `.github/workflows/pr-review.yml` to your repository
2. Go to **Repo → Settings → Secrets and variables → Actions → New repository secret**
3. Add secret:
   - Name: `PRISM_AI_URL`
   - Value: `https://your-server:8000` (your PRism-AI backend URL)
4. The workflow will automatically trigger on pull request events and send webhook to your PRism-AI backend

**Note:** Ensure your PRism-AI backend is publicly accessible or use a VPN/tunnel service like ngrok for development.

## 🐳 Docker Deployment

```bash
# Build image
docker build -t prism-ai:latest .

# Run with env file
docker run -d \
  --name prism-ai \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/config:/app/config \
  prism-ai:latest
```

### Docker Compose (with Ollama)

```yaml
version: '3.8'
services:
  prism-ai:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    volumes:
      - ./config:/app/config
    depends_on:
      - ollama

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  ollama_data:
```

---

## ☸️ Kubernetes / Helm

```bash
helm install prism-ai ./helm/prism-ai \
  --set llm.provider=vertexai \
  --set vertexai.project=my-gcp-project \
  --set secrets.githubToken=ghp_xxx
```

For GKE Workload Identity (no key file needed):
```bash
helm install prism-ai ./helm/prism-ai \
  --set llm.provider=vertexai \
  --set vertexai.workloadIdentity.enabled=true \
  --set vertexai.workloadIdentity.serviceAccount=prism-ai-sa@my-project.iam.gserviceaccount.com
```

---

## 📁 Project Structure

```
PRism-AI/
├── app/
│   ├── main.py                 # FastAPI entrypoint
│   ├── webhooks/
│   │   ├── github.py           # GitHub webhook handler
│   │   ├── gitlab.py           # GitLab webhook handler
│   │   └── gitea.py            # Gitea webhook handler
│   ├── review/
│   │   ├── engine.py           # Core review logic
│   │   ├── prompt.py           # Prompt builder
│   │   └── parser.py           # LLM response parser
│   ├── llm/
│   │   ├── router.py           # LLM provider router
│   │   ├── ollama.py           # Ollama client
│   │   ├── openai_client.py    # OpenAI client
│   │   ├── vertexai_client.py  # Vertex AI client
│   │   ├── bedrock_client.py   # AWS Bedrock client
│   │   └── azure_client.py     # Azure OpenAI client
│   ├── policy/
│   │   ├── engine.py           # Policy enforcement
│   │   └── rbac.py             # RBAC logic
│   └── evolution/
│       └── prompt_evolution.py # Self-improving prompts
├── config/
│   ├── rbac.yaml               # RBAC configuration
│   └── policy.yaml             # Review policies
├── helm/
│   └── prism-ai/               # Helm chart
├── tests/
│   ├── test_webhooks.py
│   ├── test_review.py
│   └── test_llm_router.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🧪 Running Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v --cov=app
```

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'Add my feature'`
4. Push and open a PR — PRism-AI will review it! 🎉

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for code style and guidelines.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🌟 Star History

If PRism-AI helps your team, please ⭐ the repo!

---

*Built with ❤️ for open-source teams, DevOps engineers, and developers who believe code review should be fast, consistent, and intelligent.*
