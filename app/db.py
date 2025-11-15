# app/db.py
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base

# אם לא מוגדר DATABASE_URL -> נופלים ל-SQLite (לדמו מקומי)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./slhton.db")

# ל-SQLite צריך connect_args מיוחדים, לפוסטגרס – לא
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """
    יצירת כל הטבלאות אם הן לא קיימות (users, wallets, txs, transfers, orders)
    """
    Base.metadata.create_all(bind=engine)
