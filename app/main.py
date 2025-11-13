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

# יצירת הטבלאות אם לא קיימות
Base.metadata.create_all(bind=engine)

# אפליקציית FastAPI
app = FastAPI(title="SLHTON API", version="1.0.0")

# יוצרים את ה-Application של הבוט פעם אחת
telegram_app = get_application()


@app.on_event("startup")
async def on_startup() -> None:
    """
    אירוע אתחול של FastAPI – כאן אנחנו מאתחלים ומפעילים את Application של טלגרם.
    """
    logger.info("Initializing Telegram Application on startup...")
    # אם כבר מאותחל/רץ – לא ניפול, פשוט נדלג
    if not getattr(telegram_app, "_initialized", False):
        await telegram_app.initialize()
    if not getattr(telegram_app, "running", False):
        await telegram_app.start()
    logger.info("Telegram Application initialized and started.")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """
    אירוע כיבוי – עצירה מסודרת של הבוט.
    """
    logger.info("Shutting down Telegram Application...")
    try:
        if getattr(telegram_app, "running", False):
            await telegram_app.stop()
        if getattr(telegram_app, "_initialized", False):
            await telegram_app.shutdown()
    finally:
        logger.info("Telegram Application stopped and shutdown.")


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
    """
    נקודת webhook שמקבלת עדכונים מטלגרם ומעבירה אותם ל-Application.

    כדי להבטיח יציבות מוחלטת, גם אם משום מה אירוע ה-startup לא רץ / הבוט עושה reload,
    אנחנו דואגים לוודא כאן שה-Application מאותחל ורץ לפני process_update.
    """
    # דאבל-סייפטי: לוודא initialize + start גם אם מסיבה כלשהי זה לא קרה ב-startup
    if not getattr(telegram_app, "_initialized", False):
        logger.warning("Telegram Application not initialized – initializing lazily in webhook...")
        await telegram_app.initialize()

    if not getattr(telegram_app, "running", False):
        logger.warning("Telegram Application not running – starting lazily in webhook...")
        await telegram_app.start()

    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)

    return JSONResponse({"ok": True})
