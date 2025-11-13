# app/models.py

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from .db import Base


class User(Base):
    """
    משתמש טלגרם במערכת.
    כל משתמש יכול להחזיק מספר ארנקים (למרות שבפועל אנחנו משתמשים כרגע באחד).
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # חשוב: BigInteger כדי לתמוך ב-Telegram ID גדול (כמו 7757102350)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # יחסים
    wallets = relationship("Wallet", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User id={self.id} tg={self.telegram_id} username={self.username!r}>"


class Wallet(Base):
    """
    ארנק לוגי של משתמש (דמו / off-chain).
    מאפשר החזקת יתרת SLH ועקיבת העברות בטבלה Transfer.
    """

    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # כתובת לוגית (למשל: SLH-<telegram_id>-SLH)
    address = Column(String(255), unique=True, index=True, nullable=False)

    # יתרה מדויקת – Numeric כדי לשמור כמויות קריפטו בצורה בטוחה
    balance = Column(Numeric(precision=30, scale=8), default=Decimal("0"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user = relationship("User", back_populates="wallets")

    outgoing_transfers = relationship(
        "Transfer",
        foreign_keys="Transfer.from_wallet_id",
        back_populates="from_wallet",
    )
    incoming_transfers = relationship(
        "Transfer",
        foreign_keys="Transfer.to_wallet_id",
        back_populates="to_wallet",
    )

    def __repr__(self) -> str:
        return f"<Wallet id={self.id} addr={self.address} balance={self.balance}>"


class Transfer(Base):
    """
    תיעוד העברות SLH בין ארנקים:
    - faucet
    - deposit (דמו)
    - send בין משתמשים
    - future: תשלום עבור פקודות / matching וכו'
    """

    __tablename__ = "transfers"

    id = Column(Integer, primary_key=True, index=True)

    # faucet יכול להיות בלי from_wallet_id (None)
    from_wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=True)
    to_wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)

    amount = Column(Numeric(precision=30, scale=8), nullable=False)

    # סוג ההעברה: faucet / deposit / send / order_fill / וכו'
    transfer_type = Column(String(50), nullable=False)

    # מזהה חיצוני עתידי (tx hash on-chain, reference וכו')
    tx_ref = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    from_wallet = relationship(
        "Wallet",
        foreign_keys=[from_wallet_id],
        back_populates="outgoing_transfers",
    )
    to_wallet = relationship(
        "Wallet",
        foreign_keys=[to_wallet_id],
        back_populates="incoming_transfers",
    )

    def __repr__(self) -> str:
        return (
            f"<Transfer id={self.id} "
            f"from={self.from_wallet_id} to={self.to_wallet_id} "
            f"amount={self.amount} type={self.transfer_type}>"
        )


class Order(Base):
    """
    פקודת קנייה/מכירה בסיסית (demo orderbook).
    כרגע לוגיקה פשוטה – אתה יכול להרחיב בהמשך למערכת מסחר מלאה.
    """

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    side = Column(String(4), nullable=False)  # "buy" / "sell"
    token = Column(String(50), nullable=False, default="SLH")

    amount = Column(Numeric(precision=30, scale=8), nullable=False)
    price = Column(Numeric(precision=30, scale=8), nullable=False)

    status = Column(
        String(20),
        nullable=False,
        default="open",  # open / filled / cancelled
    )

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user = relationship("User", back_populates="orders")

    def __repr__(self) -> str:
        return (
            f"<Order id={self.id} user={self.user_id} "
            f"{self.side.upper()} {self.amount} {self.token} @ {self.price} "
            f"status={self.status}>"
        )
