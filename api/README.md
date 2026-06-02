# API (FastAPI + PostgreSQL)

Backend-only guide for this repository.

## Requirements

- Python 3.10+
- PostgreSQL

## Setup

From workspace root:

```bash
pip install -r api/requirements.txt
```

Configure `api/.env` (preferred). Legacy fallback to root `.env` is supported during migration.

## Run API

From workspace root (recommended):

```bash
python -m api.app.run
```

From inside `api/` directory:

```bash
python -m app.run
```

Optional env vars: `HOST`, `PORT`, `RELOAD`.

## Alembic Migrations

From workspace root:

```bash
alembic -c api/alembic.ini upgrade head
```

Useful commands:

```bash
alembic -c api/alembic.ini current
alembic -c api/alembic.ini history
```

## Tests

From workspace root:

```bash
pytest api/tests -v
```

From inside `api/`:

```bash
pytest -v
```

## API Docs and Health

- Swagger: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- Health: <http://localhost:8000/health>

## Storage Path

Uploaded ticket images remain in `fileserver/storage/` at workspace root.  
`LOCAL_STORAGE_PATH` can override this if needed.
