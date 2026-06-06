# NetWorkspace

AI-native recruitment intelligence workspace for site onboarding, crawling, historical data accumulation, analytics, and personal AI-assisted tooling.

## Positioning

This project is a clean-slate rebuild of the legacy recruitment crawler project.

Goals:

- Keep the valuable core idea: turn short-lived job-site data into long-term analyzable historical assets.
- Rebuild with a maintainable frontend/backend architecture.
- Support official templates, personal templates, and AI-assisted site onboarding.
- Isolate user customization in personal workspaces instead of changing the core system directly.

## Naming

- Product: `NetWorkspace`
- Crawling engine: `SpiderCore`
- AI assistant: `Todd`
- Repository: `net-workspace`

## Project Structure

```text
net-workspace/
  README.md
  .gitignore
  docs/
    PRD.md
    LEGACY_REFERENCE.md
    REPOSITORY_SETUP.md
  frontend/
  backend/
    app/
  spiders/
  tests/
  archive/
```

## Recommended Stack

- Frontend: React + TypeScript + Vite + Ant Design + ECharts
- Backend: FastAPI + SQLAlchemy 2.0 + Pydantic + Alembic
- Queue: Redis + Celery or RQ
- Database: PostgreSQL preferred, MySQL 8 acceptable
- Crawling: Playwright + Requests + BeautifulSoup/lxml
- AI layer: LLM + multimodal page understanding + RAG knowledge base

## Current Status

This repository currently contains:

- an initial project folder split from legacy files
- an initial PRD aligned to the NetWorkspace concept
- a legacy-value extraction note
- GitHub setup instructions

## Immediate Next Steps

1. Connect and push to the GitHub repository `Crescent-Starling/net-workspace`.
2. Push this clean project skeleton.
3. Add architecture design doc.
4. Add database schema design doc.
5. Scaffold frontend and backend apps.

## Legacy Project Handling

Do not continue development in the old directories directly.

Legacy folders remain outside this new project root and should only be used as reference material until selected files are deliberately migrated.
