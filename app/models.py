# app/models.py
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Integer,
    BigInteger,
    Numeric,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    # מפתח פנימי לדמו
    id = Column(BigInteger, primary_key=True, index=True)

    # מזהה טלגרם אמיתי – חייב BIGINT
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)

    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # קשרים
    wallets = relationship("Wallet", back_populates="user")
    orders = relationship("Order", back_populates="user")


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)

    # כרגע ארנק פנימי בסגנון SLH-<telegram_id>-SLH
    address = Column(String(255), nullable=False, unique=True, index=True)

    # מאפשר בעתיד כמה טוקנים
    token_symbol = Column(String(32), nullable=False, default="SLH")

    # יתרת הדמו
    balance = Column(Numeric(18, 8), nullable=False, default=0)

    # קשרים
    user = relationship("User", back_populates="wallets")
    orders = relationship("Order", back_populates="wallet")
    txs = relationship("Tx", back_populates="wallet")
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


class Tx(Base):
    """
    רישום תנועות (faucet, העברות, הפקדות וכו')
    """

    __tablename__ = "txs"

    id = Column(BigInteger, primary_key=True, index=True)
    wallet_id = Column(BigInteger, ForeignKey("wallets.id"), nullable=False, index=True)

    amount = Column(Numeric(18, 8), nullable=False)
    token_symbol = Column(String(32), nullable=False, default="SLH")

    # אפשר להשתמש כ־"faucet", "transfer", "deposit" וכו'
    note = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    wallet = relationship("Wallet", back_populates="txs")


class Transfer(Base):
    """
    טבלת העברות בין ארנקים (send)
    """

    __tablename__ = "transfers"

    id = Column(BigInteger, primary_key=True, index=True)

    from_wallet_id = Column(
        BigInteger, ForeignKey("wallets.id"), nullable=False, index=True
    )
    to_wallet_id = Column(
        BigInteger, ForeignKey("wallets.id"), nullable=False, index=True
    )

    amount = Column(Numeric(18, 8), nullable=False)
    token_symbol = Column(String(32), nullable=False, default="SLH")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    from_wallet = relationship(
        "Wallet", foreign_keys=[from_wallet_id], back_populates="outgoing_transfers"
    )
    to_wallet = relationship(
        "Wallet", foreign_keys=[to_wallet_id], back_populates="incoming_transfers"
    )


class Order(Base):
    """
    הזמנות קניה/מכירה (order)
    """

    __tablename__ = "orders"

    id = Column(BigInteger, primary_key=True, index=True)

    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    wallet_id = Column(BigInteger, ForeignKey("wallets.id"), nullable=False, index=True)

    # "buy" / "sell"
    side = Column(String(4), nullable=False)

    token_symbol = Column(String(32), nullable=False, default="SLH")
    amount = Column(Numeric(18, 8), nullable=False)
    price = Column(Numeric(18, 8), nullable=False)

    is_open = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="orders")
    wallet = relationship("Wallet", back_populates="orders")
