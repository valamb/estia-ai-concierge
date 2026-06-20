# 🏨 ESTIA — AI Multimodal Hotel Concierge Assistant

> An intelligent, multilingual AI concierge assistant for luxury hotels, powered by OpenAI and Retrieval-Augmented Generation (RAG).

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-orange.svg)](https://openai.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20Store-purple.svg)](https://www.trychroma.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📖 Overview

**ESTIA** is a final university project demonstrating the application of modern AI technologies in the hospitality industry. It serves as a digital concierge for luxury hotel properties, capable of answering guest questions in both **Greek** and **English** about hotel services, restaurants, spa, sports, transportation, and more.

The system uses **Retrieval-Augmented Generation (RAG)** to ground its answers in real hotel knowledge base documents, ensuring accurate, property-specific responses.

---

## ✨ Features

- 🌍 **Multilingual** — Greek and English support
- 🤖 **AI-Powered** — OpenAI GPT-4o integration
- 📚 **RAG Architecture** — ChromaDB vector store for hotel knowledge
- 🗣️ **Multimodal** — Text chat (voice and image planned)
- 🏨 **Hotel-Specific** — Covers restaurants, spa, sports, kids club, transportation, VIP services
- ⚡ **REST API** — FastAPI backend
- 🧪 **Tested** — Unit and integration test suite

---

## 🏗️ Project Structure

```
estia-ai-concierge/
├── app/                    # Core application code
│   ├── api/                # FastAPI route handlers
│   ├── core/               # Configuration, logging, startup
│   ├── services/           # Business logic (AI, RAG, chat)
│   ├── models/             # Pydantic data models
│   └── utils/              # Shared utility functions
├── knowledge/              # Hotel knowledge base documents
│   ├── properties/         # Hotel property information
│   ├── restaurants/        # Restaurant menus & details
│   ├── bars/               # Bar information
│   ├── spa/                # Spa services & treatments
│   ├── sports/             # Sports & activities
│   ├── family/             # Kids club & family services
│   ├── transportation/     # Transport options
│   └── premium/            # VIP & yacht services
├── static/                 # Frontend assets (CSS, JS, images)
├── docs/                   # Project documentation
├── examples/               # Usage examples & demo scripts
├── tests/                  # Test suite
├── .env.example            # Environment variable template
├── .gitignore              # Git ignore rules
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/estia-ai-concierge.git
cd estia-ai-concierge

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and add your API keys
```

### Running the Application

```bash
uvicorn app.main:app --reload
```

Open your browser at `http://localhost:8000`

---

## 🏨 Supported Properties

- **Porto Elounda** — Luxury resort & spa
- **Elounda Mare** — Relais & Châteaux hotel
- **Elounda Peninsula** — All-suite luxury resort

---

## 📚 Documentation

| Document | Description |
|---|---|
| [Architecture](docs/architecture.md) | System design & component overview |
| [Setup Guide](docs/setup_guide.md) | Detailed installation instructions |
| [Development Guide](docs/development_guide.md) | Contribution & coding standards |
| [RAG Design](docs/rag_design.md) | Retrieval-Augmented Generation pipeline |
| [Knowledge Base](docs/knowledge_base_design.md) | Hotel data structure & ingestion |
| [Roadmap](docs/roadmap.md) | Planned features & milestones |

---

## 🗺️ Roadmap

- [x] Phase 1 — Project Foundation & Architecture
- [ ] Phase 2 — FastAPI Application Skeleton
- [ ] Phase 3 — OpenAI Integration & Chat
- [ ] Phase 4 — RAG Pipeline & ChromaDB
- [ ] Phase 5 — Knowledge Base Ingestion
- [ ] Phase 6 — Greek Language Support
- [ ] Phase 7 — Voice Interaction
- [ ] Phase 8 — Image Recognition
- [ ] Phase 9 — Frontend UI
- [ ] Phase 10 — Deployment

---

## 🧑‍💻 Author

**Lambros** — University Final Project, 2025–2026

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
