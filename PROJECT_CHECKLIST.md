# Project Progress Checklist

> Use this markdown checklist to track the **actual** work completed on Abandoned-Products.  
> Tick items with `[x]` as they are finished; leave `[ ]` for pending.

---

## 1. Environment & Bootstrapping

- [ ] Create local Python virtualenv (`python -m venv .venv && source .venv/bin/activate`)
- [ ] Upgrade `pip` inside the env
- [ ] Install **modern** dependencies (`requirements.txt`)
- [ ] (Optional) Install **legacy** dependencies
- [ ] Run initial DB migrations (`python manage.py migrate`)
- [ ] Seed demo data (`populate_sample_data`)
- [ ] Verify dev server boots on http://localhost:8000

## 2. Tooling Setup

- [ ] Add/verify `Makefile` with `dev` and `test` targets
- [ ] Configure `ruff` (lint + formatter) project-wide
- [ ] Configure `black` & `isort` (handled via ruff)  
- [ ] Enable `mypy --strict` in `schooldriver-modern` (CI optional)

## 3. Testing Pipeline

- [ ] Add / update unit tests for new code
- [ ] Ensure `python manage.py test` passes locally
- [ ] Integrate tests + lint step in CI (GitHub Actions or similar)

## 4. Sub-Agent Readiness

- [ ] SearchAgent functional (codebase_search works)
- [ ] DjangoAgent able to run migrations & tests
- [ ] AngularAgent wired to `components/` folder
- [ ] DocsAgent can write & commit Mermaid diagrams
- [ ] DataAgent allowed to exec SQL in dev DB

## 5. Security Hardening

- [ ] No secrets or `.env` committed to Git
- [ ] `.env.example` exists & is documented
- [ ] `django-environ` (or equivalent) parsing env vars in settings
- [ ] HTTPS enforced in production settings

## 6. Configuration Governance

- [ ] New config keys documented in README & AGENT.md
- [ ] Default settings guarded by `os.getenv()`
- [ ] Config changes mirrored in `.env.example`

## 7. Definition of Done Validation

- [ ] All tests green & lint clean (`ruff check .`)
- [ ] `python manage.py check` passes
- [ ] Migrations committed when models change
- [ ] Frontend lint (`npm run lint` under `components/`) passes if JS touched
- [ ] AGENT.md updated when conventions evolve

## 8. Miscellaneous / Nice-to-Haves

- [ ] Set up Postgres docker-compose service for local testing
- [ ] Configure Celery + Redis for async tasks
- [ ] Add circle diagrams for admissions & grade workflow (DocsAgent)
- [ ] Migrate remaining critical features from legacy to modern codebase

---

_Last updated: <!-- TODO: update date when editing -->_ 