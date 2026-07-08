# ESTIA — Development Guide

## Project Conventions

### Python Style
- Formatter: **Black** (line length 88)
- Linter: **Ruff**
- Type hints: required on all public functions
- Docstrings: short one-line summary for all public classes and functions

### File Naming
- Python files: `snake_case.py`
- Folders: `snake_case/`
- Knowledge documents: `snake_case.md` or `snake_case.pdf`

---

## Branching Strategy

```
main            → Production-ready, protected branch
│
├── develop     → Integration branch, all features merge here
│   │
│   ├── feature/phase-2-fastapi-skeleton
│   ├── feature/phase-3-openai-chat
│   ├── feature/phase-4-rag-pipeline
│   └── feature/phase-5-knowledge-base
│
└── hotfix/     → Critical bug fixes branched directly from main
```

### Rules
- Never commit directly to `main`
- Open a Pull Request from `feature/*` → `develop`
- Merge `develop` → `main` only for releases

---

## Commit Message Convention

Format: `<type>(<scope>): <short description>`

| Type | When to use |
|---|---|
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `docs` | Documentation only changes |
| `refactor` | Code restructuring, no behavior change |
| `test` | Adding or updating tests |
| `chore` | Tooling, dependencies, configuration |
| `style` | Formatting, no logic change |

### Examples
```
feat(chat): add multi-turn conversation history
fix(rag): handle empty ChromaDB query results
docs(readme): add installation instructions
chore(deps): upgrade openai to 1.54.3
test(api): add chat endpoint integration tests
```

---

## Running Code Quality Tools

```bash
# Format code
black .

# Lint
ruff check .

# Type check
mypy app/

# Run tests
pytest tests/ -v
```

---

## Adding a New Feature

1. Create branch: `git checkout -b feature/your-feature develop`
2. Implement and write tests
3. Run `black .` and `ruff check .`
4. Commit using the convention above
5. Open a Pull Request to `develop`

---

## Conversation-Level Guest Context Memory

ESTIA extracts and remembers guest context within a single conversation session.
Context is stored in memory only — it disappears when the application restarts.
No database, Redis, cookies or persistent profiles are used.

### How it works

On every incoming message at `POST /api/v1/chat`:

1. The existing `GuestContext` for the `conversation_id` is loaded from `conversation_store`.
2. `extract_context(message)` runs rule-based extraction on the raw message text (no LLM call).
3. The old and new contexts are merged with `merge_context()` — scalar fields take the newer value; list fields (interests, dietary preferences, children ages) are unioned.
4. The merged context is saved back to `conversation_store`.
5. `chat_service.chat()` receives the context and appends a `## Known Guest Context` block to the system prompt, after the RAG context block and before conversation history.
6. Empty contexts (all fields None / empty lists) are silently skipped — nothing is appended.

### GuestContext fields

| Field | Type | Example |
|---|---|---|
| `property` | `str \| None` | `"porto_elounda"` |
| `guest_type` | `str \| None` | `"family"`, `"honeymoon"`, `"couple"`, `"vip"` |
| `children_ages` | `list[int]` | `[5, 8]` |
| `interests` | `list[str]` | `["spa", "beach"]` |
| `occasion` | `str \| None` | `"anniversary"`, `"birthday"`, `"proposal"` |
| `preferred_language` | `str \| None` | `"en"`, `"el"` |
| `dietary_preferences` | `list[str]` | `["vegetarian", "halal"]` |
| `mobility_needs` | `str \| None` | `"wheelchair"` |

### Relevant files

| File | Purpose |
|---|---|
| `app/models/chat.py` | `GuestContext` Pydantic model |
| `app/services/context_extraction.py` | `extract_context`, `merge_context`, `format_context_block` |
| `app/services/conversation_store.py` | `get_context`, `save_context`, `clear_context` |
| `app/services/chat_service.py` | Injects context block into system prompt |
| `app/api/routes/chat.py` | Orchestrates extract → merge → save → pass per request |

### Running Phase D tests

```bash
# All Phase D offline tests (59 tests, no API key needed)
pytest tests/test_context_extraction.py tests/test_conversation_store_context.py tests/test_chat_integration_context.py -v
```
