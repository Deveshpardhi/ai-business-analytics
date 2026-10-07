# AI Business Analytics

Phase 1 is a deterministic FastAPI analytics backend. It requires Python 3.10+
(the current development environment is Python 3.13).

```bash
python -m venv backend/.venv
source backend/.venv/bin/activate
python -m pip install -r backend/requirements.txt
pytest -q
```

Set `DATABASE_URL` in `.env` before starting the API. The provided
`docker-compose.yml` defines the development PostgreSQL service.

## Grounded LLM explanations

Optional business-language explanations use the OpenAI Responses API. Configure
the following variables in `.env` (see `.env.example`):

```text
LLM_PROVIDER=openai
LLM_MODEL=your-supported-text-model
OPENAI_API_KEY=your_api_key
```

Only verified analytical evidence is sent to the provider. Missing provider
configuration or a provider failure marks an explanation as unavailable without
affecting deterministic analysis results.

## Frontend

The React/Vite frontend lives in `frontend`. It uses `http://localhost:8000` by
default; override this with `VITE_API_BASE_URL` when needed. Start it with:

```bash
cd frontend
npm install
npm run dev
```

The backend allows the Vite development origin by default. Set
`CORS_ALLOW_ORIGINS` to a comma-separated allowlist for another frontend origin.

Apply the schema before starting the application:

```bash
alembic upgrade head
```

Alembic reads `DATABASE_URL` through the existing application settings. For an
already-created, unversioned development database, review the schema and run
`alembic stamp head` only after confirming it matches the initial migration.
`backend/app/db/init_db.py` remains a legacy local/test helper and is not the
production schema-management path.

GitHub Actions starts an isolated PostgreSQL service, applies the migrations,
checks that model metadata has no pending migration operations, and runs the
test suite. Local unit tests do not require Docker; set `DATABASE_URL` to a
PostgreSQL database only when you want to exercise migrations against it.

[![Architecture diagram](https://gitdiagram.com/diagram-badge.svg)](https://gitdiagram.com/deveshpardhi/ai-business-analytics?utm_source=readme&utm_medium=badge)

