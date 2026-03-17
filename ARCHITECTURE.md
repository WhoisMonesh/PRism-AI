# PRism AI Architecture

## System Overview

PRism AI is a modular, plugin-based PR review automation platform with three main layers:

1. **Integration Layer** - Git providers + Webhooks
2. **Orchestration Layer** - Review engine + Policy enforcement
3. **Execution Layer** - LLM backends + Agent tools

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     EXTERNAL TRIGGERS                     │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────────┐   │
│  │ GitHub  │  │ GitLab  │  │  Gitea  │  │ Web UI   │   │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬─────┘   │
│       │            │            │            │          │
│       └────────────┴────────────┴────────────┘          │
│                         │                                │
│                    Webhook POST                          │
└─────────────────────────┼────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────┐
│                    API GATEWAY (FastAPI)                  │
│  ┌────────────────┐  ┌─────────────┐  ┌──────────────┐  │
│  │ /webhook/*     │  │ /api/v1/*   │  │ /api/v1/    │  │
│  │  - GitHub      │  │  - review   │  │  - health   │  │
│  │  - GitLab      │  │  - settings │  │  - feedback │  │
│  │  - Gitea       │  │  - models   │  │             │  │
│  └───────┬────────┘  └──────┬──────┘  └──────┬───────┘  │
│          │                  │                │          │
│          └──────────────────┴────────────────┘          │
│                         │                                │
│                  CORS + Auth Middleware                  │
└─────────────────────────┼────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────┐
│                   CORE ORCHESTRATION                      │
│  ┌────────────────────────────────────────────────────┐  │
│  │              ReviewEngine                          │  │
│  │  - Validates request                               │  │
│  │  - Checks policy                                   │  │
│  │  - Fetches PR data                                 │  │
│  │  - Routes to agent                                 │  │
│  │  - Posts results                                   │  │
│  └───────────┬────────────────────────┬────────────────┘  │
│              │                        │                   │
│  ┌───────────▼─────────┐  ┌──────────▼─────────────┐    │
│  │   PolicyEngine      │  │  PromptEvolution       │    │
│  │  - Repo patterns    │  │  - Feedback tracking   │    │
│  │  - Tool whitelist   │  │  - Score analytics     │    │
│  │  - Min scores       │  │  - Prompt improvement  │    │
│  │  - Blocked files    │  │                        │    │
│  └─────────────────────┘  └────────────────────────┘    │
└─────────────────────────┼────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────┐
│                    AGENT TOOLS (10)                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │  review  │ │ security │ │   perf   │ │  improve │   │
│  └─────┬────┘ └─────┬────┘ └─────┬────┘ └─────┬────┘   │
│        │            │            │            │         │
│  ┌─────▼────┐ ┌────▼─────┐ ┌────▼─────┐ ┌────▼─────┐   │
│  │ describe │ │changelog │ │   ask    │ │  labels  │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│  ┌──────────┐ ┌──────────┐                              │
│  │ test_gen │ │self_review│                             │
│  └──────────┘ └──────────┘                              │
│                         │                                │
│              All agents use LLMClient                    │
└─────────────────────────┼────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────┐
│              LLM BACKENDS (Pluggable)                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │  Ollama  │ │  Vertex  │ │ Bedrock  │ │  OpenAI  │   │
│  │  Local   │ │    AI    │ │  Claude  │ │  GPT-4   │   │
│  └─────┬────┘ └─────┬────┘ └─────┬────┘ └─────┬────┘   │
│        │            │            │            │         │
│  ┌─────▼────────────▼────────────▼────────────▼─────┐   │
│  │           LLMClient Interface                    │   │
│  │  - generate(prompt) -> response                  │   │
│  │  - health_check() -> bool                        │   │
│  │  - get_model_name() -> str                       │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────┼────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────┐
│              GIT PROVIDER CLIENTS (4)                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │  GitHub  │ │  GitLab  │ │  Gitea   │ │Bitbucket │   │
│  └─────┬────┘ └─────┬────┘ └─────┬────┘ └─────┬────┘   │
│        │            │            │            │         │
│  ┌─────▼────────────▼────────────▼────────────▼─────┐   │
│  │           GitProvider Interface                  │   │
│  │  - get_pr_diff()                                 │   │
│  │  - get_pr_files()                                │   │
│  │  - post_pr_comment()                             │   │
│  │  - post_inline_comments()                        │   │
│  │  - create_review()                               │   │
│  │  - add_labels()                                  │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

## Data Flow: Webhook → Review → Post

```
1. PR opened/updated in GitHub
        ↓
2. GitHub sends webhook POST
        ↓
3. FastAPI /webhook/github endpoint
        ↓
4. Verify HMAC signature
        ↓
5. Parse event (PR number, repo, owner)
        ↓
6. Background task: process_webhook()
        ↓
7. ReviewEngine.execute_review()
        ↓
8. PolicyEngine: check allowed tools/models
        ↓
9. GitHubProvider: fetch PR diff + files
        ↓
10. Filter blocked files (vendor/, etc.)
        ↓
11. ReviewAgent: build prompt
        ↓
12. LLMClient.generate(prompt)
        ↓
        ┌────────────┐
        │ Ollama/    │
        │ Vertex/    │
        │ Bedrock    │
        └─────┬──────┘
              ↓
13. Parse JSON response → ReviewResult
        ↓
14. Apply min_score threshold
        ↓
15. GitHubProvider.create_review()
        ↓
16. Post inline comments (path + line)
        ↓
17. Add labels (if enabled)
        ↓
18. ✅ Review posted to PR
```

## Component Breakdown

### 1. Backend API (`backend/main.py`)

**Responsibilities:**
- HTTP endpoint routing
- Webhook signature verification
- Background task queue
- CORS middleware
- Error handling

**Key Endpoints:**
- `POST /api/v1/review` - Manual review trigger
- `POST /api/v1/webhook/{provider}` - Webhook receivers
- `GET /api/v1/health` - System health
- `GET/POST /api/v1/settings` - Config management

### 2. Review Engine (`backend/core/review_engine.py`)

**Responsibilities:**
- Orchestrate review workflow
- Policy enforcement
- Agent selection
- Result aggregation

**Flow:**
```python
async def execute_review(request: ReviewRequest) -> ReviewResult:
    1. Check policy (is tool allowed?)
    2. Get Git provider client
    3. Fetch PR diff + files
    4. Filter blocked files
    5. Select + run agent
    6. Return result
```

### 3. Policy Engine (`backend/core/policy_engine.py`)

**Responsibilities:**
- Load `policy.yaml`
- Match repo patterns (glob-style)
- Enforce tool/model restrictions
- Filter blocked files
- Apply score thresholds

**Example Policy:**
```yaml
- repo_pattern: "org/critical-*"
  allowed_tools: ["review", "security"]
  min_score: 90
  blocked_patterns: ["*.lock", "dist/*"]
```

### 4. LLM Backends (`backend/llm_backends/`)

**Interface:**
```python
class LLMClient(ABC):
    @abstractmethod
    async def generate(prompt: str, temperature: float, max_tokens: int) -> str

    @abstractmethod
    async def health_check() -> bool

    @abstractmethod
    def get_model_name() -> str
```

**Implementations:**
- **OllamaBackend** - HTTP to local Ollama API
- **VertexBackend** - Google Cloud AI Platform SDK
- **BedrockBackend** - AWS Boto3 + IAM
- **OpenAIBackend** - OpenAI API or compatible

### 5. Git Providers (`backend/git_providers/`)

**Interface:**
```python
class GitProvider(ABC):
    @abstractmethod
    async def verify_webhook(payload: bytes, signature: str) -> bool

    @abstractmethod
    async def get_pr_diff(owner, repo, number) -> str

    @abstractmethod
    async def post_pr_comment(owner, repo, number, body) -> None

    @abstractmethod
    async def create_review(owner, repo, number, result) -> None
```

**Implementations:**
- **GitHubProvider** - GitHub REST API v3
- **GitLabProvider** - GitLab API v4
- **GiteaProvider** - Gitea API
- **BitbucketProvider** - Bitbucket Cloud API

### 6. Agent Tools (`backend/agents/`)

Each agent:
1. Receives `diff` + `files`
2. Builds specialized prompt
3. Calls `llm.generate()`
4. Parses/formats response
5. Returns result

**Example (ReviewAgent):**
```python
async def run(diff: str, files: list[dict]) -> ReviewResult:
    prompt = self._build_prompt(diff, files)
    response = await self.llm.generate(prompt)
    return self._parse_json_response(response)
```

## Security Architecture

### 1. Webhook Verification

```python
# GitHub
HMAC-SHA256(secret, payload) == X-Hub-Signature-256

# GitLab
secret == X-Gitlab-Token
```

### 2. No Hardcoded Secrets

All credentials via:
- Environment variables (`.env`)
- Secret managers (AWS Secrets Manager, GCP Secret Manager)
- IAM roles (Vertex Workload Identity, Bedrock STS)

### 3. Policy Enforcement

```
Request → PolicyEngine.get_policy(repo)
        → Check allowed_tools
        → Check min_score
        → Filter blocked files
        → ✅ or ❌
```

### 4. Network Isolation

For intranet/airgapped deployments:
```
Docker Network: prism-net (bridge)
  ├── prism-ai (backend)
  ├── ollama (LLM)
  └── frontend

Firewall rules:
  - Inbound: 8000, 5173 only from internal network
  - Outbound: DENY * (fully offline mode)
```

## Deployment Architectures

### Local Development

```
┌──────────────────┐
│   Developer      │
│   Laptop         │
│  ┌────────────┐  │
│  │Docker      │  │
│  │Compose     │  │
│  │ ├─ Backend │  │
│  │ ├─ Ollama  │  │
│  │ └─ Frontend│  │
│  └────────────┘  │
└──────────────────┘
```

### Production (Cloud)

```
┌────────────────────────────────────┐
│         Load Balancer (HTTPS)      │
└───────────┬────────────────────────┘
            ↓
┌───────────▼────────────────────────┐
│      K8s Cluster / ECS             │
│  ┌──────────────┐  ┌─────────────┐│
│  │ PRism AI     │  │  Frontend   ││
│  │ (3 replicas) │  │  (Nginx)    ││
│  └──────┬───────┘  └─────────────┘│
│         │                          │
│         ↓                          │
│  ┌─────────────────────┐          │
│  │  Vertex AI / Bedrock│          │
│  │  (External)         │          │
│  └─────────────────────┘          │
└────────────────────────────────────┘
```

### Intranet (Airgapped)

```
┌────────────────────────────────────┐
│      Internal Network              │
│  ┌──────────────┐  ┌─────────────┐│
│  │ PRism AI     │  │  Ollama     ││
│  │              │  │  (GPU)      ││
│  └──────┬───────┘  └─────────────┘│
│         │                          │
│         ↓                          │
│  ┌─────────────────────┐          │
│  │  Gitea (Self-hosted)│          │
│  └─────────────────────┘          │
│                                    │
│  No Internet Access                │
└────────────────────────────────────┘
```

## Performance Considerations

### 1. Async I/O
All network calls use `async/await`:
```python
async with httpx.AsyncClient() as client:
    resp = await client.get(...)
```

### 2. Background Tasks
Webhooks processed in background:
```python
@app.post("/webhook/github")
async def webhook(background_tasks: BackgroundTasks):
    background_tasks.add_task(process_webhook, payload)
    return {"status": "accepted"}
```

### 3. Prompt Compression
Large diffs truncated:
```python
diff[:8000]  # First 8K chars
```

### 4. Caching
Future: Add Redis for:
- PR diff caching
- Review result caching
- Rate limit counters

## Extensibility

### Adding New LLM Backend

1. Implement `LLMClient` interface
2. Add to `llm_backends/__init__.py`
3. Add config vars to `config.py`
4. Update frontend dropdown

### Adding New Agent Tool

1. Create `agents/your_tool.py`
2. Implement `run(diff, files)` method
3. Add to `review_engine.py` tool router
4. Update frontend tool selector

### Adding New Git Provider

1. Implement `GitProvider` interface
2. Add webhook endpoint in `main.py`
3. Add to `get_git_provider()` factory
4. Add config vars

## Monitoring & Observability

Future enhancements:
- Prometheus metrics (`/metrics`)
- Structured logging (JSON)
- Distributed tracing (OpenTelemetry)
- Error tracking (Sentry)

## Diagram Prompt for Visualization Tools

Use this prompt with Eraser.io, Lucidchart AI, or Mermaid:

> Create a detailed layered software architecture diagram for PRism-AI, a self-hosted AI Pull Request review agent. Include these components grouped by layer with directional data-flow arrows and color coding per layer:
>
> LAYER 1 — EXTERNAL TRIGGERS (blue):
> - Developer opens/updates a Pull Request on GitHub, GitLab, or Gitea
> - Webhook POST sent to PRism-AI backend (HMAC-SHA256 signed)
> - Optional: manual review triggered from Web UI
>
> LAYER 2 — WEB UI (indigo):
> - React + Tailwind SPA served at http://localhost:5173
> - Dashboard: LLM health indicator, connected provider name
> - Review Panel: input repo/PR number, select provider, trigger review, view score ring
> - Settings Panel: change LLM provider/model/URL, approval threshold, auto-review toggle
> - Results View: comments grouped by severity (critical=red, warning=amber, info=blue, suggestion=green)
>
> LAYER 3 — API GATEWAY (slate):
> - FastAPI app on port 8000
> - Routes: POST /api/v1/webhook/github, POST /api/v1/review, GET/POST /api/v1/settings, GET /api/v1/health, GET /api/v1/models
> - CORS middleware, background task queue for async webhook processing
>
> LAYER 4 — CORE ENGINE (purple):
> - WebhookHandler: signature verification, event routing
> - ReviewEngine: builds structured prompt, calls LLM, parses JSON response into ReviewResult (score 0-100, approved bool, comments with path/line/severity/category/suggestion)
> - PolicyEngine: RBAC rules, blocked file patterns, minimum score thresholds, severity overrides
> - PromptEvolution: stores feedback, self-improves prompts over time, cron-based scheduling
> - SettingsManager: hot-reload config from env / .env file
>
> LAYER 5 — LLM BACKENDS (orange, pluggable via config):
> - OllamaBackend → local Ollama REST API at http://ollama:11434
> - OllamaCloudBackend → cloud Ollama endpoint with API key
> - VertexBackend → GCP Vertex AI Gemini via service account JSON or Workload Identity
> - BedrockBackend → AWS Bedrock (Claude/Titan) via IAM access keys or role ARN
> - OpenAIBackend → OpenAI API or any OpenAI-compatible endpoint (vLLM, LM Studio, etc.)
>
> LAYER 6 — GIT PROVIDERS (green):
> - GitHubProvider: fetch diff/PR info/files, post PR review with inline comments, add labels, approve/request changes, verify HMAC webhook signature
> - GitLabProvider: fetch MR diff, post inline discussion notes, MR-level notes
> - (Extensible: GiteaProvider, BitbucketProvider stubs)
>
> LAYER 7 — INFRASTRUCTURE (gray):
> - Docker Compose: prism-ai container + ollama container on bridge network prism-net
> - Volumes: ollama_data (model persistence), prism_data (SQLite DB, evolution store)
> - Secrets: GCP service account JSON mounted read-only at /secrets/gcp-sa.json
> - Optional: NVIDIA GPU passthrough to Ollama for local inference
> - Healthcheck: HTTP poll to /api/v1/health every 30s
>
> DATA FLOW (show as numbered arrows):
> 1. Developer pushes PR → GitHub sends webhook to FastAPI
> 2. WebhookHandler verifies HMAC → spawns background task
> 3. ReviewEngine fetches diff + PR info from GitHubProvider
> 4. ReviewEngine sends prompt to selected LLM Backend
> 5. LLM returns JSON review → parsed into ReviewResult
> 6. PolicyEngine applies rules → final ReviewResult
> 7. GitHubProvider posts inline comments + PR review event + labels
> 8. Results also shown in Web UI when triggered manually
>
> Show all 7 layers as horizontal bands with components as boxes inside. Use distinct colors per layer. Draw arrows between layers showing the data flow.
