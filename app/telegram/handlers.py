# app/telegram/handlers.py
from typing import List

from telegram import Update
from telegram.ext import ContextTypes

from ..db import SessionLocal
from ..config import settings
from .. import models
from ..services import users as users_service
from ..services import wallet as wallet_service
from ..services import orders as orders_service


# ============================
# Helpers
# ============================
def _format_user(user: models.User) -> str:
    parts: List[str] = []
    if user.first_name:
        parts.append(user.first_name)
    if user.last_name:
        parts.append(user.last_name)
    display_name = " ".join(parts) or "Unknown"
    if user.username:
        display_name += f" (@{user.username})"
    return display_name


def _get_or_create_current_user_and_wallet(update: Update) -> tuple[models.User, models.Wallet]:
    tg_user = update.effective_user
    if tg_user is None:
        raise RuntimeError("No effective Telegram user in update")

    db = SessionLocal()
    try:
        user = users_service.get_or_create_user(
            db=db,
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
        )
        wallet = wallet_service.get_or_create_wallet(db, user=user)
        db.expunge(user)
        db.expunge(wallet)
        return user, wallet
    finally:
        db.close()


# ============================
# Commands
# ============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "ברוך הבא ל-SLHTON demo!\n"
        "הפקודות הזמינות:\n"
        "/whoami - פרטי המשתמש שלך\n"
        "/wallet - יצירת ארנק והצגת יתרה\n"
        "/deposit <amount> - הפקדה דמו\n"
        "/order <buy|sell> <token> <amount> <price> - יצירת הזמנה\n"
        "/orders - צפייה בהזמנות פתוחות\n"
        "/faucet - קבלת טוקנים חינמיים\n"
        "/send <@user|telegram_id> <amount> - שליחת SLH למשתמש אחר\n"
        "/adminpanel - לפקודות אדמין"
    )
    await update.effective_message.reply_text(text)


async def whoami(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = update.effective_user
    if tg_user is None:
        return

    db = SessionLocal()
    try:
        user = users_service.get_or_create_user(
            db=db,
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
        )
        text = (
            f"ID פנימי: {user.id}\n"
            f"Telegram ID: {user.telegram_id}\n"
            f"Username: @{user.username}" if user.username else "Username: (אין)\n"
        )
        await update.effective_message.reply_text(text)
    finally:
        db.close()


async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = SessionLocal()
    try:
        tg_user = update.effective_user
        if tg_user is None:
            await update.effective_message.reply_text("לא הצלחתי לזהות משתמש.")
            return

        user = users_service.get_or_create_user(
            db=db,
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
        )
        wallet = wallet_service.get_or_create_wallet(db, user=user)

        await update.effective_message.reply_text(
            f"כתובת ארנק: {wallet.address}\n"
            f"יתרה: {wallet.balance} {wallet.token_symbol}"
        )
    finally:
        db.close()


async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.effective_message.reply_text("שימוש: /deposit <amount>")
        return

    try:
        amount = float(context.args[0])
    except ValueError:
        await update.effective_message.reply_text("amount חייב להיות מספר.")
        return

    if amount <= 0:
        await update.effective_message.reply_text("הסכום חייב להיות גדול מאפס.")
        return

    db = SessionLocal()
    try:
        tg_user = update.effective_user
        if tg_user is None:
            await update.effective_message.reply_text("לא הצלחתי לזהות משתמש.")
            return

        user = users_service.get_or_create_user(
            db=db,
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
        )
        wallet = wallet_service.get_or_create_wallet(db, user=user)
        tx = wallet_service.deposit(db=db, wallet=wallet, amount=amount)

        await update.effective_message.reply_text(
            f"הופקדו {tx.amount} {tx.token_symbol}. "
            f"יתרה חדשה: {wallet.balance}"
        )
    except ValueError as e:
        await update.effective_message.reply_text(str(e))
    finally:
        db.close()


async def faucet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = SessionLocal()
    try:
        tg_user = update.effective_user
        if tg_user is None:
            await update.effective_message.reply_text("לא הצלחתי לזהות משתמש.")
            return

        user = users_service.get_or_create_user(
            db=db,
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
        )
        wallet = wallet_service.get_or_create_wallet(db, user=user)
        tx = wallet_service.faucet(db=db, wallet=wallet)

        await update.effective_message.reply_text(
            f"התקבלו {tx.amount} {tx.token_symbol}. יתרה: {wallet.balance}"
        )
    finally:
        db.close()


async def order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 4:
        await update.effective_message.reply_text(
            "שימוש: /order <buy|sell> <token> <amount> <price>"
        )
        return

    side, token_symbol, amount_str, price_str = context.args

    try:
        amount = float(amount_str)
        price = float(price_str)
    except ValueError:
        await update.effective_message.reply_text("amount ו-price חייבים להיות מספרים.")
        return

    db = SessionLocal()
    try:
        tg_user = update.effective_user
        if tg_user is None:
            await update.effective_message.reply_text("לא הצלחתי לזהות משתמש.")
            return

        user = users_service.get_or_create_user(
            db=db,
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
        )

        order = orders_service.create_order(
            db=db,
            user=user,
            side=side,
            token_symbol=token_symbol,
            amount=amount,
            price=price,
        )

        await update.effective_message.reply_text(
            "הזמנה נוצרה בהצלחה:\n"
            f"ID: {order.id}\n"
            f"Side: {order.side}\n"
            f"Token: {order.token_symbol}\n"
            f"Amount: {order.amount}\n"
            f"Price: {order.price}"
        )
    except ValueError as e:
        await update.effective_message.reply_text(str(e))
    finally:
        db.close()


async def orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = SessionLocal()
    try:
        open_orders = orders_service.list_open_orders(db=db)
        if not open_orders:
            await update.effective_message.reply_text("אין הזמנות פתוחות.")
            return

        lines = ["הזמנות פתוחות:"]
        for o in open_orders:
            lines.append(
                f"#{o.id} {o.side.upper()} {o.amount} {o.token_symbol} @ {o.price}"
            )
        await update.effective_message.reply_text("\n".join(lines))
    finally:
        db.close()


async def adminpanel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = update.effective_user
    if tg_user is None:
        return

    if tg_user.id not in settings.admin_owner_ids:
        await update.effective_message.reply_text("אין לך הרשאת אדמין.")
        return

    text = (
        "Admin Panel\n"
        "- /orders - צפייה בהזמנות\n"
        "- (ניתן להרחיב לפקודות נוספות בהמשך)"
    )
    await update.effective_message.reply_text(text)


async def send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /send <@username|telegram_id> <amount>
    שולח SLH ממשתמש אחד לשני.
    """
    if len(context.args) != 2:
        await update.effective_message.reply_text(
            "שימוש: /send <@username|telegram_id> <amount>"
        )
        return

    target_raw, amount_str = context.args

    try:
        amount = float(amount_str)
    except ValueError:
        await update.effective_message.reply_text("amount חייב להיות מספר.")
        return

    if amount <= 0:
        await update.effective_message.reply_text("הסכום חייב להיות גדול מאפס.")
        return

    tg_user = update.effective_user
    if tg_user is None:
        await update.effective_message.reply_text("לא הצלחתי לזהות משתמש שולח.")
        return

    db = SessionLocal()
    try:
        # שולח
        sender = users_service.get_or_create_user(
            db=db,
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
        )
        sender_wallet = wallet_service.get_or_create_wallet(db=db, user=sender)

        # יעד לפי username או telegram_id
        target_user = None
        # אם יש @ – ניקוי
        clean = target_raw.lstrip("@")

        # ננסה קודם כטלגרם ID
        try:
            tid = int(clean)
            target_user = users_service.get_user_by_telegram_id(db=db, telegram_id=tid)
        except ValueError:
            #
