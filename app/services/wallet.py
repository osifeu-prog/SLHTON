# app/services/wallet.py
from sqlalchemy.orm import Session

from .. import models
from ..config import settings


def get_or_create_wallet(
    db: Session,
    user: models.User,
    token_symbol: str | None = None,
) -> models.Wallet:
    if token_symbol is None:
        token_symbol = settings.faucet_token

    wallet = (
        db.query(models.Wallet)
        .filter(
            models.Wallet.user_id == user.id,
            models.Wallet.token_symbol == token_symbol,
        )
        .first()
    )

    if wallet is None:
        wallet = models.Wallet(
            user_id=user.id,
            address=f"SLH-{user.telegram_id}-{token_symbol}",
            token_symbol=token_symbol,
            balance=0.0,
        )
        db.add(wallet)
        db.commit()
        db.refresh(wallet)

    return wallet


def deposit(
    db: Session,
    wallet: models.Wallet,
    amount: float,
    tx_type: str = "deposit",
    description: str | None = None,
) -> models.Tx:
    if amount <= 0:
        raise ValueError("Amount must be positive")

    wallet.balance += amount
    tx = models.Tx(
        wallet_id=wallet.id,
        tx_type=tx_type,
        amount=amount,
        token_symbol=wallet.token_symbol,
        description=description or "",
    )

    db.add(tx)
    db.commit()
    db.refresh(wallet)
    db.refresh(tx)
    return tx


def faucet(
    db: Session,
    wallet: models.Wallet,
    faucet_amount: float | None = None,
) -> models.Tx:
    amount = float(faucet_amount or settings.faucet_amount)
    return deposit(
        db=db,
        wallet=wallet,
        amount=amount,
        tx_type="faucet",
        description="Faucet airdrop",
    )


def transfer(
    db: Session,
    from_wallet: models.Wallet,
    to_wallet: models.Wallet,
    amount: float,
    token_symbol: str | None = None,
) -> tuple[models.Wallet, models.Wallet, models.Tx, models.Tx]:
    """
    העברת טוקנים בין שני ארנקים באותה מטבע.
    יוצרת 2 שורות Tx: send + receive.
    """
    if amount <= 0:
        raise ValueError("הסכום חייב להיות גדול מאפס.")

    if token_symbol is None:
        token_symbol = settings.faucet_token

    if from_wallet.token_symbol != token_symbol or to_wallet.token_symbol != token_symbol:
        raise ValueError("ארנקים לא תואמים למטבע המבוקש.")

    if from_wallet.id == to_wallet.id:
        raise ValueError("אי אפשר לשלוח לעצמך.")

    if from_wallet.balance < amount:
        raise ValueError("אין מספיק יתרה בארנק השולח.")

    # עדכון יתרות
    from_wallet.balance -= amount
    to_wallet.balance += amount

    tx_out = models.Tx(
        wallet_id=from_wallet.id,
        tx_type="send",
        amount=amount,
        token_symbol=token_symbol,
        description=f"Send to wallet {to_wallet.address}",
    )
    tx_in = models.Tx(
        wallet_id=to_wallet.id,
        tx_type="receive",
        amount=amount,
        token_symbol=token_symbol,
        description=f"Receive from wallet {from_wallet.address}",
    )

    db.add_all([tx_out, tx_in])
    db.commit()

    db.refresh(from_wallet)
    db.refresh(to_wallet)
    db.refresh(tx_out)
    db.refresh(tx_in)

    return from_wallet, to_wallet, tx_out, tx_in
