# Setup Guide

This guide walks through setting up PRism AI from scratch for different deployment scenarios.

## Table of Contents
1. [Local Development Setup](#local-development-setup)
2. [Production Deployment](#production-deployment)
3. [Intranet Deployment](#intranet-deployment)
4. [Cloud Deployment](#cloud-deployment)

## Local Development Setup

### Step 1: Install Prerequisites

**macOS:**
```bash
brew install docker docker-compose git
```

**Linux:**
```bash
sudo apt update
sudo apt install docker.io docker-compose git
sudo usermod -aG docker $USER
```

**Windows:**
- Install Docker Desktop from https://docker.com
- Install Git from https://git-scm.com

### Step 2: Clone Repository

```bash
git clone https://github.com/WhoisMonesh/PRism-AI.git
cd PRism-AI
```

### Step 3: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your favorite editor:
```bash
# Minimum required for local dev
GITHUB_TOKEN=ghp_YOUR_TOKEN_HERE
GITHUB_WEBHOOK_SECRET=any_random_string_here
LLM_PROVIDER=ollama
AUTO_REVIEW_ON_PR=false
```

**To get GitHub token:**
1. Go to https://github.com/settings/tokens
2. Generate new token (classic)
3. Select scopes: `repo`, `read:org`
4. Copy token to `.env`

### Step 4: Start Services

```bash
docker-compose up -d
```

Check logs:
```bash
docker-compose logs -f prism-ai
```

### Step 5: Initialize Ollama

Pull a model:
```bash
docker exec -it ollama ollama pull llama3.1
```

Recommended models:
- `llama3.1` - General purpose (4GB)
- `qwen2.5-coder` - Code-focused (4.7GB)
- `codellama` - Code generation (3.8GB)

### Step 6: Verify

Open http://localhost:5173

You should see the PRism AI dashboard. Check:
- Dashboard shows "Healthy" status
- LLM Backend shows "Available"
- GitHub shows "Connected" (if token is valid)

### Step 7: Test Manual Review

1. Go to **Review** tab
2. Fill in:
   - Provider: GitHub
   - Owner: `facebook`
   - Repo: `react`
   - PR Number: `27500` (or any recent PR)
   - Tool: Review
3. Click "Run Review"
4. Wait 30-60 seconds for results

## Production Deployment

### Option 1: Docker Compose with Traefik

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  traefik:
    image: traefik:v2.10
    command:
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.myresolver.acme.tlschallenge=true"
      - "--certificatesresolvers.myresolver.acme.email=admin@example.com"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./letsencrypt:/letsencrypt
    networks:
      - prism-net

  prism-ai:
    build: .
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.prism.rule=Host(`prism.example.com`)"
      - "traefik.http.routers.prism.entrypoints=websecure"
      - "traefik.http.routers.prism.tls.certresolver=myresolver"
    env_file:
      - .env.prod
    volumes:
      - ./data:/app/data
    networks:
      - prism-net
    depends_on:
      - ollama

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_data:/root/.ollama
    networks:
      - prism-net
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

volumes:
  ollama_data:

networks:
  prism-net:
    driver: bridge
```

Deploy:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Option 2: Kubernetes with Helm

Install Helm chart:
```bash
helm repo add prism-ai https://whoismonesh.github.io/PRism-AI/helm
helm install prism prism-ai/prism-ai \
  --set ingress.enabled=true \
  --set ingress.host=prism.example.com \
  --set github.token=$GITHUB_TOKEN \
  --set llm.provider=vertex \
  --set vertex.projectId=$GCP_PROJECT
```

## Intranet Deployment

For completely offline/airgapped environments:

### Step 1: Prepare Air-Gapped Images

On internet-connected machine:
```bash
docker pull ollama/ollama:latest
docker pull your-registry/prism-ai:latest

docker save ollama/ollama:latest | gzip > ollama.tar.gz
docker save your-registry/prism-ai:latest | gzip > prism-ai.tar.gz
```

### Step 2: Transfer to Intranet

Copy `ollama.tar.gz`, `prism-ai.tar.gz`, and project files to intranet server.

### Step 3: Load Images

```bash
docker load < ollama.tar.gz
docker load < prism-ai.tar.gz
```

### Step 4: Configure for Intranet

Edit `.env`:
```bash
# Use Gitea or self-hosted GitLab
GITEA_TOKEN=your_token
GITEA_BASE_URL=https://git.intranet.company.com
GITEA_WEBHOOK_SECRET=your_secret

# Local Ollama only
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.1

# No external CORS
CORS_ORIGINS=["http://localhost:5173","http://prism.intranet.company.com"]
```

### Step 5: Deploy

```bash
docker-compose up -d
```

### Step 6: Pull Models (One-Time)

Download models on internet-connected machine:
```bash
ollama pull llama3.1
tar -czf llama-models.tar.gz ~/.ollama/models
```

Transfer to intranet and extract:
```bash
tar -xzf llama-models.tar.gz -C /var/lib/docker/volumes/prism-ai_ollama_data/_data/
```

## Cloud Deployment

### AWS (using Bedrock)

1. Create IAM role with Bedrock permissions
2. Launch EC2 instance with IAM role attached
3. Install Docker
4. Configure `.env`:

```bash
LLM_PROVIDER=bedrock
BEDROCK_REGION=us-east-1
BEDROCK_MODEL=anthropic.claude-3-sonnet-20240229-v1:0
# IAM role authentication - no keys needed
```

5. Deploy:
```bash
docker-compose up -d
```

### GCP (using Vertex AI)

1. Create service account with Vertex AI User role
2. Create GCE instance
3. Mount service account JSON:

```bash
gcloud iam service-accounts keys create /tmp/sa.json \
  --iam-account=prism-ai@PROJECT_ID.iam.gserviceaccount.com
```

4. Configure `.env`:
```bash
LLM_PROVIDER=vertex
VERTEX_PROJECT_ID=my-project-123
VERTEX_LOCATION=us-central1
VERTEX_MODEL=gemini-1.5-pro
VERTEX_CREDENTIALS_PATH=/secrets/gcp-sa.json
```

5. Deploy with secret mount:
```bash
docker run -d \
  -v /tmp/sa.json:/secrets/gcp-sa.json:ro \
  --env-file .env \
  -p 8000:8000 \
  prism-ai:latest
```

### Azure (using OpenAI)

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=$AZURE_OPENAI_KEY
OPENAI_BASE_URL=https://YOUR_RESOURCE.openai.azure.com/openai/deployments/YOUR_DEPLOYMENT
OPENAI_MODEL=gpt-4
```

## Troubleshooting

### Ollama Not Responding

```bash
docker exec -it ollama ollama list
docker logs ollama
```

If empty, pull models:
```bash
docker exec -it ollama ollama pull llama3.1
```

### Backend Crashes on Startup

Check logs:
```bash
docker logs prism-ai
```

Common issues:
- Missing `.env` file → copy from `.env.example`
- Invalid credentials → check GitHub token
- Port 8000 in use → change `PORT` in `.env`

### Webhook Returns 401

Signature mismatch. Ensure `GITHUB_WEBHOOK_SECRET` in `.env` matches webhook secret in GitHub settings.

### LLM Timeout

Increase timeout for large PRs:

Edit `backend/llm_backends/ollama_backend.py`:
```python
async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minutes
```

### Out of Memory (Ollama)

Use smaller model:
```bash
docker exec -it ollama ollama pull phi
```

Or increase Docker memory limit in Docker Desktop settings.

## Next Steps

After deployment, see:
- [README.md](README.md) for API reference
- [policy.yaml](policy.yaml) for RBAC examples
- [CONTRIBUTING.md](CONTRIBUTING.md) for development guide
