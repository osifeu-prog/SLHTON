import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


# אם יש DATABASE_URL (למשל PostgreSQL בריילווי) – נשתמש בו.
# אחרת ניפול חזרה ל-SQLite מקומי.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./slhton.db")


connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    # דרוש רק ל-SQLite
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
