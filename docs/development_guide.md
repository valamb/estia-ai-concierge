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
