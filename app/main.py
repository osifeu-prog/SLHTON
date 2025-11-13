import logging
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from telegram import Update

from .config import settings
from .db import Base, engine
from .telegram import get_application

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# יצירת טבלאות אם לא קיימות
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SLHTON API", version="1.0.0")

@app.get("/health")
async def health() -> Dict[str, Any]:
    return {"status": "ok"}

@app.get("/meta")
async def meta() -> Dict[str, Any]:
    return {
        "service": "SLHTON",
        "public_base_url": settings.public_base_url,
        "admin_owner_ids": settings.admin_owner_ids,
    }

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    """נקודת webhook שמקבלת עדכונים מטלגרם ומעבירה אותם ל-Application."""
    app_bot = get_application()
    data = await request.json()
    update = Update.de_json(data, app_bot.bot)
    await app_bot.process_update(update)
    return JSONResponse({"ok": True})
