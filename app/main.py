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

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SLHTON API", version="1.0.0")

telegram_app = get_application()


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("Initializing Telegram Application...")
    await telegram_app.initialize()
    await telegram_app.start()
    logger.info("Telegram Application initialized and started.")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("Shutting down Telegram Application...")
    await telegram_app.stop()
    await telegram_app.shutdown()
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
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return JSONResponse({"ok": True})
