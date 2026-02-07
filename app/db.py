import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Env is loaded in app.config (load_dotenv from project root). The app entry point
# (app.main) must import app.config before app.db so DATABASE_URL is available.

# Prefer env var so credentials are not in code. In production set DATABASE_URL.
# Example: postgresql+psycopg2://user:password@localhost:5432/dbname
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:173674a@localhost:5432/garaza",
)

# Log SQL only when SQL_ECHO is set (e.g. "true"); off by default to avoid noise and leakage in production
_sql_echo = os.getenv("SQL_ECHO", "false").strip().lower() in ("true", "1", "yes")
engine = create_engine(DATABASE_URL, echo=_sql_echo)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Base(DeclarativeBase):
    pass
