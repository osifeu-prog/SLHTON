from telegram.ext import Application, CommandHandler

from ..config import settings
from . import handlers

_application: Application | None = None


def get_application() -> Application:
    global _application
    if _application is not None:
        return _application

    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is not set")

    app = Application.builder().token(settings.bot_token).build()

    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(CommandHandler("whoami", handlers.whoami))
    app.add_handler(CommandHandler("wallet", handlers.wallet))
    app.add_handler(CommandHandler("deposit", handlers.deposit))
    app.add_handler(CommandHandler("faucet", handlers.faucet))
    app.add_handler(CommandHandler("order", handlers.order))
    app.add_handler(CommandHandler("orders", handlers.orders))
    app.add_handler(CommandHandler("adminpanel", handlers.adminpanel))

    _application = app
    return app
