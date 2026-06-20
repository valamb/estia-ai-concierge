# ESTIA — Setup Guide

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.11+ | [python.org](https://python.org) |
| pip | latest | Included with Python |
| Git | any | [git-scm.com](https://git-scm.com) |
| OpenAI API Key | — | [platform.openai.com](https://platform.openai.com) |

---

## Step 1 — Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/estia-ai-concierge.git
cd estia-ai-concierge
```

---

## Step 2 — Create a Virtual Environment

```bash
# Create
python -m venv venv

# Activate (macOS / Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

You should see `(venv)` at the start of your terminal prompt.

---

## Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Step 4 — Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` in a text editor and fill in your values:

```env
OPENAI_API_KEY=sk-your-real-key-here
```

> **Warning:** Never share your `.env` file or commit it to Git.

---

## Step 5 — Run the Application

```bash
uvicorn app.main:app --reload
```

The API will be available at:
- Application: `http://localhost:8000`
- API Docs (Swagger): `http://localhost:8000/docs`
- API Docs (ReDoc): `http://localhost:8000/redoc`

---

## Step 6 — (Future) Ingest the Knowledge Base

```bash
python -m app.scripts.ingest_knowledge
```

This reads all documents from `knowledge/` and loads them into ChromaDB.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError` | Make sure your virtual environment is activated |
| `OPENAI_API_KEY not set` | Check your `.env` file exists and has the key |
| Port 8000 already in use | Run with `--port 8001` |
