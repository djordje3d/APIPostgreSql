# API (FastAPI + PostgreSQL)

Backend-only guide for this repository.

## Requirements

- Python 3.10+
- PostgreSQL

## Setup

From workspace root:

```bash
pip install -r api_python/requirements.txt
```

Configure `api_python/.env` (preferred). Legacy fallback to root `.env` is supported during migration.

## Run API

From workspace root (recommended):

```bash
python -m api_python.app.run
```

From inside `api_python/` directory:

```bash
python -m app.run
```

Optional env vars: `HOST`, `PORT`, `RELOAD`.

## Alembic Migrations

From workspace root:

```bash
alembic -c api_python/alembic.ini upgrade head
```

Useful commands:

```bash
alembic -c api_python/alembic.ini current
alembic -c api_python/alembic.ini history
```

## Tests

From workspace root:

```bash
pytest api_python/tests -v
```

From inside `api_python/`:

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

