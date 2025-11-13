from sqlalchemy.orm import Session
from telegram import Update
from telegram.ext import ContextTypes

from ..db import SessionLocal
from ..services import users as users_service
from ..services import wallet as wallet_service
from ..services import orders as orders_service
from ..config import settings


def _get_db() -> Session:
    return SessionLocal()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = _get_db()
    try:
        tg_user = update.effective_user
        users_service.get_or_create_user(
            db,
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
        )
        text = (
            "ברוך הבא ל-SLHTON demo!\n"
            "הפקודות הזמינות:\n"
            "/whoami - פרטי המשתמש שלך\n"
            "/wallet - יצירת ארנק והצגת יתרה\n"
            "/deposit <amount> - הפקדה דמו\n"
            "/order <buy|sell> <token> <amount> <price> - יצירת הזמנה\n"
            "/orders - צפייה בהזמנות פתוחות\n"
            "/faucet - קבלת טוקנים חינמיים\n"
            "/adminpanel - לפקודות אדמין"
        )
        await update.effective_message.reply_text(text)
    finally:
        db.close()


async def whoami(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = _get_db()
    try:
        tg_user = update.effective_user
        user = users_service.get_or_create_user(
            db,
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
        )
        text = (
            f"ID פנימי: {user.id}\n"
            f"Telegram ID: {user.telegram_id}\n"
            f"Username: @{user.username}\n"
            f"שם: {user.first_name}"
        )
        await update.effective_message.reply_text(text)
    finally:
        db.close()


async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = _get_db()
    try:
        tg_user = update.effective_user
        user = users_service.get_or_create_user(
            db,
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
        )
        wallet = wallet_service.get_or_create_wallet(db, user)
        text = (
            f"כתובת ארנק: {wallet.address}\n"
            f"יתרה: {wallet.balance} {wallet.token_symbol}"
        )
        await update.effective_message.reply_text(text)
    finally:
        db.close()


async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.effective_message.reply_text("שימוש: /deposit <amount>")
        return

    try:
        amount = float(context.args[0])
    except ValueError:
        await update.effective_message.reply_text("הכמות חייבת להיות מספר.")
        return

    db = _get_db()
    try:
        tg_user = update.effective_user
        user = users_service.get_or_create_user(
            db,
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
        )
        wallet = wallet_service.get_or_create_wallet(db, user)
        wallet = wallet_service.deposit(db, wallet, amount)
        text = f"הופקדו {amount} {wallet.token_symbol}. יתרה חדשה: {wallet.balance}"
        await update.effective_message.reply_text(text)
    finally:
        db.close()


async def faucet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = _get_db()
    try:
        tg_user = update.effective_user
        user = users_service.get_or_create_user(
            db,
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
        )
        wallet = wallet_service.get_or_create_wallet(db, user)
        wallet = wallet_service.faucet(db, wallet)
        text = f"התקבלו {settings.faucet_amount} {wallet.token_symbol}. יתרה: {wallet.balance}"
        await update.effective_message.reply_text(text)
    finally:
        db.close()


async def order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 4:
        await update.effective_message.reply_text(
            "שימוש: /order <buy|sell> <token> <amount> <price>"
        )
        return

    side = context.args[0]
    token = context.args[1]
    try:
        amount = float(context.args[2])
        price = float(context.args[3])
    except ValueError:
        await update.effective_message.reply_text("amount ו-price חייבים להיות מספרים.")
        return

    db = _get_db()
    try:
        tg_user = update.effective_user
        user = users_service.get_or_create_user(
            db,
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
        )
        try:
            order_obj = orders_service.create_order(
                db,
                user=user,
                side=side,
                token_symbol=token,
                amount=amount,
                price=price,
            )
        except ValueError as e:
            await update.effective_message.reply_text(str(e))
            return

        text = (
            "הזמנה נוצרה בהצלחה:\n"
            f"ID: {order_obj.id}\n"
            f"Side: {order_obj.side}\n"
            f"Token: {order_obj.token_symbol}\n"
            f"Amount: {order_obj.amount}\n"
            f"Price: {order_obj.price}"
        )
        await update.effective_message.reply_text(text)
    finally:
        db.close()


async def orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = _get_db()
    try:
        open_orders = orders_service.list_open_orders(db)
        if not open_orders:
            await update.effective_message.reply_text("אין הזמנות פתוחות כרגע.")
            return
        lines = ["הזמנות פתוחות:"]
        for o in open_orders[:20]:
            lines.append(
                f"#{o.id} {o.side.upper()} {o.amount} {o.token_symbol} @ {o.price}"
            )
        await update.effective_message.reply_text("\n".join(lines))
    finally:
        db.close()


async def adminpanel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = update.effective_user
    if tg_user.id not in settings.admin_owner_ids:
        await update.effective_message.reply_text("אין לך הרשאת אדמין.")
        return

    text = (
        "Admin Panel\n"
        "- /orders - צפייה בהזמנות\n"
        "- (ניתן להרחיב לפקודות נוספות בהמשך)"
    )
    await update.effective_message.reply_text(text)
