from sqlalchemy.orm import Session
from .. import models
from ..config import settings

def get_or_create_wallet(db: Session, user: models.User, token_symbol: str = "SLH") -> models.Wallet:
    wallet = (
        db.query(models.Wallet)
        .filter(models.Wallet.user_id == user.id, models.Wallet.token_symbol == token_symbol)
        .first()
    )
    if wallet:
        return wallet

    # יצירת "כתובת" דמו מבוססת ID
    address = f"SLH-{user.telegram_id}-{token_symbol}"
    wallet = models.Wallet(
        user_id=user.id,
        address=address,
        token_symbol=token_symbol,
        balance=0.0,
    )
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return wallet

def deposit(db: Session, wallet: models.Wallet, amount: float, token_symbol: str = "SLH") -> models.Wallet:
    wallet.balance += amount
    tx = models.Tx(
        wallet_id=wallet.id,
        tx_type="deposit",
        amount=amount,
        token_symbol=token_symbol,
    )
    db.add(tx)
    db.commit()
    db.refresh(wallet)
    return wallet

def faucet(db: Session, wallet: models.Wallet) -> models.Wallet:
    amount = float(settings.faucet_amount)
    return deposit(db, wallet, amount, settings.faucet_token)
