# Abandoned-Products Project

Abandoned-Products is a mono-repo that currently hosts **two** Django codebases plus legacy frontend assets.

1. **`schooldriver`** – legacy production system (Django 1.7, Angular 1.x)
2. **`schooldriver-modern`** – ongoing rewrite (Django 4.2, DRF)

Unless a task explicitly targets the legacy tree, all new work should land in **schooldriver-modern**.

---

## Build & Commands

```bash
# Bootstrap once
python -m venv .venv && source .venv/bin/activate && pip install -U pip

# Install deps (modern app)
pip install -r schooldriver-modern/requirements.txt

# (Optional) install legacy deps
pip install -r schooldriver/core-requirements.txt -r schooldriver/dev-requirements.txt

# Migrate & seed demo data
python schooldriver-modern/manage.py migrate
python schooldriver-modern/manage.py populate_sample_data

# Start dev server
python schooldriver-modern/manage.py runserver 0.0.0.0:8000

# Run tests (all modern apps)
python schooldriver-modern/manage.py test

# Lint & type-check
ruff check .

# Auto-format
ruff format .
```

Shortcuts provided by an optional `Makefile`:

```
make dev   # runserver
make test  # modern tests
```

### Development Environment

- Django dev server: http://localhost:8000
- Static files served from `/static/`
- SQLite database (`db.sqlite3`) by default; Postgres in production (port 5432)

---

## Code Style

Python
- Black (88 chars) + isort
- `ruff check .` as the single linter (includes flake8, pycodestyle, etc.)
- mypy strict in modern code; legacy exempt

JavaScript / Angular
- 2-space indent, semicolons **required**
- Keep using Angular 1.x & vanilla JS — **do not introduce new frameworks**

Docs
- Markdown wrapped at 120 chars
- Mermaid diagrams for flows

---

## Testing

- Django `TestCase` + factory-boy for fixtures
- Tests live next to code (`tests/` sub-package)
- CI: run `python manage.py test && ruff check .` before every commit
- Sub-agents MUST repair any failing tests they introduce

---

## Architecture

- Backend: Django 4.2, Django REST Framework (for modern path)
- Legacy backend: Django 1.7 (`ecwsp/` modules) – read-only unless specified
- Frontend assets (Angular 1.x, Sass) under `components/`, `static_files/`, `templates/`
- Database: SQLite (dev), PostgreSQL (prod)
- Task queue (future): Celery + Redis

### 🚫 Legacy Code Freeze

**ABSOLUTE RULE** – Files and directories under `schooldriver/` (legacy project) are *immutable*.  
AI agents (Amp, Cursor sub-agents, etc.) MUST **never** create, edit, move, or delete anything inside that path unless the human maintainer explicitly instructs so in the prompt.  Any attempted change should be aborted with an error.

### Sub-Agent Catalogue (Amp specific)

| Sub-Agent | Primary Tools | Typical Tasks |
|-----------|---------------|---------------|
| **SearchAgent** | `codebase_search`, `grep_search` | Locate models, views, templates |
| **DjangoAgent** | `read_file`, `edit_file`, `run_terminal_cmd` | Add models, migrations, serializers, run tests |
| **AngularAgent** | `read_file`, `edit_file` | Modify JS/Sass/html in `components/` |
| **DocsAgent** | `create_diagram`, `edit_file` | Update `/docs`, write Mermaid diagrams |
| **DataAgent** | `run_terminal_cmd` | DB queries, bulk data fixes |

Spawn sub-agents for discrete units of work to maximise parallelism.

---

## Security

- **Never** commit secrets or `.env` files
- Use environment variables for DB creds in production
- Validate all user inputs (DRF serializers & Django forms)
- HTTPS in production

---

## Git Workflow

1. Create feature branch off `main`
2. Ensure `ruff check .` & `python manage.py test` pass **before** committing
3. Avoid `git push --force`; use `--force-with-lease` only on personal branches
4. Keep commits focused; squash trivial fix-ups

---

## Configuration

When a new setting or env variable is added:
1. Document it in `README.md` **and** update this file
2. Add default to `schooldriver_modern/settings.py` guarded by `os.getenv()`
3. Include example in `.env.example`

---

## Definition of Done

- Tests green & lint clean
- Server boots: `python manage.py check`
- Migration files committed (if models changed)
- For frontend changes: `npm run lint` under `components/` passes
- Section in AGENT.md updated if conventions change

---

## Common Pitfalls

- Migration conflicts → `python manage.py makemigrations` before edits
- Legacy `ecwsp.*` imports leaking into modern code
- Large binaries in Git

---

_This AGENT.md is the single source of truth for all AI agents (Amp, Cursor, etc.). Keep it accurate and up-to-date._ 