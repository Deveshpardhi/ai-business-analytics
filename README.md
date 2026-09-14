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
