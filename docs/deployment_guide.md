# ESTIA — Deployment Guide

## Overview

ESTIA ships as a single Docker container. ChromaDB data is persisted in a Docker volume so the knowledge base survives container restarts.

```
[ Browser ] ──HTTP──► [ estia container :8000 ]
                              │
                       /app/chroma_db  ← Docker volume (persistent)
                              │
                       /app/knowledge  ← Baked into the image
```

---

## Option 1 — Docker Compose (Recommended)

### Prerequisites
- Docker Desktop (Mac/Windows) or Docker Engine + Compose (Linux)
- OpenAI API key

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/estia-ai-concierge.git
cd estia-ai-concierge

# 2. Create your .env file
cp .env.example .env
# Set OPENAI_API_KEY=sk-... in .env

# 3. Build and start
docker compose up --build

# 4. Ingest the knowledge base (first time only)
docker compose exec estia python -m app.scripts.ingest_knowledge

# 5. Open the app
# http://localhost:8000
```

### Useful commands

```bash
# View logs
docker compose logs -f estia

# Stop
docker compose down

# Rebuild after code changes
docker compose up --build

# Re-ingest after knowledge changes
docker compose exec estia python -m app.scripts.ingest_knowledge --reset

# Delete all data (vector store)
docker compose down -v
```

---

## Option 2 — Local (No Docker)

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
cp .env.example .env           # fill in OPENAI_API_KEY

python -m app.scripts.ingest_knowledge
uvicorn app.main:app --reload
```

---

## Option 3 — Cloud Deployment

### Railway

Railway auto-detects the `Dockerfile` and deploys with one command.

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and deploy
railway login
railway init
railway up

# Set environment variable
railway variables set OPENAI_API_KEY=sk-your-key-here
```

Add a Volume in the Railway dashboard mounted at `/app/chroma_db` to persist the vector store.

### Render

1. Create a new **Web Service** on Render
2. Connect your GitHub repository
3. Set **Environment** → `Docker`
4. Add environment variable: `OPENAI_API_KEY`
5. Add a **Disk** mounted at `/app/chroma_db` (512 MB is sufficient)
6. Deploy

### Azure Container Apps

```bash
# Build and push to Azure Container Registry
az acr build --registry YOUR_REGISTRY --image estia:latest .

# Deploy
az containerapp create \
  --name estia \
  --resource-group YOUR_RG \
  --image YOUR_REGISTRY.azurecr.io/estia:latest \
  --env-vars OPENAI_API_KEY=secretref:openai-key \
  --ingress external --target-port 8000
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | **Yes** | — | Your OpenAI API key |
| `OPENAI_MODEL` | No | `gpt-4o` | Chat completion model |
| `OPENAI_EMBEDDING_MODEL` | No | `text-embedding-3-small` | Embedding model for RAG |
| `OPENAI_MAX_TOKENS` | No | `1000` | Max tokens per reply |
| `OPENAI_TEMPERATURE` | No | `0.3` | Response creativity (0–1) |
| `APP_ENV` | No | `development` | Set to `production` in cloud |
| `DEBUG` | No | `false` | Enable debug mode |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `CHROMA_DB_PATH` | No | `./chroma_db` | Vector store path |
| `RAG_TOP_K` | No | `5` | Chunks retrieved per query |
| `DEFAULT_LANGUAGE` | No | `en` | Fallback language |

---

## Production Checklist

- [ ] `OPENAI_API_KEY` set via environment (never in code or image)
- [ ] `APP_ENV=production` and `DEBUG=false`
- [ ] ChromaDB volume persisted (not ephemeral)
- [ ] Knowledge base ingested: `python -m app.scripts.ingest_knowledge`
- [ ] HTTPS enabled (handled by Railway/Render/Azure automatically)
- [ ] Health check passing: `GET /health` returns `{"status": "ok"}`

---

## Health Check

```bash
curl http://localhost:8000/health
# {"status":"ok","app_name":"ESTIA","version":"0.1.0","environment":"production"}
```

```bash
curl http://localhost:8000/info
# Shows documents_indexed count — must be > 0 after ingestion
```
