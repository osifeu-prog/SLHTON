# app/db.py
import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# -------------------------------------------------
# Database URL priority:
# 1. DATABASE_URL (Postgres ב-Railway)
# 2. SQLite מקומי לקומי/פיתוח
# -------------------------------------------------
_raw_url = os.getenv("DATABASE_URL", "").strip()

if _raw_url:
    # Railway Postgres, לדוגמה:
    # postgres://USER:PASSWORD@HOST:PORT/DB
    DATABASE_URL = _raw_url
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
else:
    # Fallback – SQLite (לוקאלי בלבד)
    DATABASE_URL = "sqlite:///./slhton.db"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency – נותן Session ומוודא סגירה בסוף."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
