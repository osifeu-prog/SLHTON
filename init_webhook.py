import logging
import sys

import httpx
import uvicorn

from app.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def set_webhook() -> None:
    if not settings.bot_token:
        logger.error("BOT_TOKEN is not set. Cannot configure webhook.")
        sys.exit(1)
    if not settings.public_base_url:
        logger.error("PUBLIC_BASE_URL is not set. Cannot configure webhook.")
        sys.exit(1)

    webhook_url = f"{settings.public_base_url}/telegram/webhook"
    api_url = f"https://api.telegram.org/bot{settings.bot_token}/setWebhook"

    logger.info("🚀 Initializing Telegram Bot Webhook")
    logger.info("🤖 Bot Token: %s...", settings.bot_token[:10])
    logger.info("🌐 Webhook URL: %s", webhook_url)

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
            sys.exit(1)
        logger.info("✅ Webhook set successfully!")


if __name__ == "__main__":
    set_webhook()
    logger.info("🎉 Bot is ready! Starting API server ...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port)
