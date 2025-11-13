import logging
from typing import Dict, Any

import httpx
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


async def _ensure_telegram_app_started() -> None:
    """
    פונקציית עזר שמוודאת שה-Application של טלגרם מאותחל ורץ.
    נשתמש בה גם ב-startup וגם ב-webhook (ליתר ביטחון).
    """
    if not getattr(telegram_app, "_initialized", False):
        logger.info("Telegram Application not initialized – initializing...")
        await telegram_app.initialize()

    if not getattr(telegram_app, "running", False):
        logger.info("Telegram Application not running – starting...")
        await telegram_app.start()


def _set_telegram_webhook() -> None:
    """
    קביעת webhook ישירות דרך Telegram API.
    זה דומה למה שהיה ב-init_webhook.py, רק משולב לתוך האפליקציה.
    """
    if not settings.bot_token:
        logger.error("BOT_TOKEN is not set. Cannot configure webhook.")
        return
    if not settings.public_base_url:
        logger.error("PUBLIC_BASE_URL is not set. Cannot configure webhook.")
        return

    webhook_url = f"{settings.public_base_url}/telegram/webhook"
    api_url = f"https://api.telegram.org/bot{settings.bot_token}/setWebhook"

    logger.info("🚀 Initializing Telegram Bot Webhook (from app.main)")
    logger.info("🤖 Bot Token: %s...", settings.bot_token[:10])
    logger.info("🌐 Webhook URL: %s", webhook_url)

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                api_url,
                json={
                    "url": webhook_url,
                    "allowed_updates": ["message", "callback_query"],
                },
            )
            data = resp.json()
            logger.info("📡 Webhook response: %s", data)
            if not data.get("ok"):
                logger.error("Failed to set webhook: %s", data)
            else:
                logger.info("✅ Webhook set successfully!")
    except Exception as e:
        logger.exception("Error while setting Telegram webhook: %s", e)


@app.on_event("startup")
async def on_startup() -> None:
    """
    אירוע אתחול של FastAPI – כאן אנחנו:
    1. מאתחלים ומפעילים את Application של טלגרם.
    2. דואגים שה-webhook יהיה מוגדר.
    """
    logger.info("=== FastAPI startup: initializing Telegram Application & webhook ===")
    await _ensure_telegram_app_started()
    _set_telegram_webhook()
    logger.info("=== Startup complete ===")


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

    אם משום מה אירוע ה-startup לא רץ (או שהשרת עשה reload),
    אנחנו דואגים כאן לוודא שהבוט מאותחל ורץ לפני process_update.
    """
    await _ensure_telegram_app_started()

    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)

    return JSONResponse({"ok": True})
