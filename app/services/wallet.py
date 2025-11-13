from sqlalchemy.orm import Session

from .. import models
from ..config import settings


def get_or_create_wallet(
    db: Session,
    user: models.User,
    token_symbol: str = "SLH",
) -> models.Wallet:
    wallet = (
        db.query(models.Wallet)
        .filter(
            models.Wallet.user_id == user.id,
            models.Wallet.token_symbol == token_symbol,
        )
        .first()
    )
    if wallet:
        return wallet

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


def deposit(
    db: Session,
    wallet: models.Wallet,
    amount: float,
    token_symbol: str = "SLH",
) -> models.Wallet:
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


def transfer(
    db: Session,
    from_wallet: models.Wallet,
    to_wallet: models.Wallet,
    amount: float,
    token_symbol: str = "SLH",
) -> tuple[models.Wallet, models.Wallet]:
    """
    העברת SLH מארנק שולח לארנק נמען.
    יוצרת Tx כפול: transfer_out + transfer_in.
    """

    if amount <= 0:
        raise ValueError("הסכום חייב להיות גדול מ-0.")

    if from_wallet.id == to_wallet.id:
        raise ValueError("אי אפשר לשלוח לעצמך.")

    if from_wallet.balance < amount:
        raise ValueError("אין מספיק יתרה בארנק לשליחה.")

    from_wallet.balance -= amount
    to_wallet.balance += amount

    tx_out = models.Tx(
        wallet_id=from_wallet.id,
        tx_type="transfer_out",
        amount=amount,
        token_symbol=token_symbol,
    )
    tx_in = models.Tx(
        wallet_id=to_wallet.id,
        tx_type="transfer_in",
        amount=amount,
        token_symbol=token_symbol,
    )

    db.add(tx_out)
    db.add(tx_in)
    db.commit()
    db.refresh(from_wallet)
    db.refresh(to_wallet)

    return from_wallet, to_wallet
