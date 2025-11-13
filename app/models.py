# app/models.py
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # מזהה טלגרם – יכול להיות מאוד גדול, לכן BigInteger
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # קשרים
    wallets = relationship(
        "Wallet",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    orders = relationship(
        "Order",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    sent_transfers = relationship(
        "Transfer",
        foreign_keys="Transfer.from_user_id",
        back_populates="from_user",
        cascade="all, delete-orphan",
    )
    received_transfers = relationship(
        "Transfer",
        foreign_keys="Transfer.to_user_id",
        back_populates="to_user",
        cascade="all, delete-orphan",
    )


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # כתובת לוגית של ארנק SLH (למשל: SLH-<telegram_id>-SLH)
    address = Column(String(255), unique=True, index=True, nullable=False)

    # איזה טוקן מחזיק הארנק – כרגע SLH, בעתיד אפשר BTC/TON וכו'
    token_symbol = Column(String(32), nullable=False, default="SLH")

    # יתרה דמו (float פשוט)
    balance = Column(Float, nullable=False, default=0.0)

    user = relationship("User", back_populates="wallets")

    outgoing_transfers = relationship(
        "Transfer",
        foreign_keys="Transfer.from_wallet_id",
        back_populates="from_wallet",
        cascade="all, delete-orphan",
    )
    incoming_transfers = relationship(
        "Transfer",
        foreign_keys="Transfer.to_wallet_id",
        back_populates="to_wallet",
        cascade="all, delete-orphan",
    )

    orders = relationship(
        "Order",
        back_populates="wallet",
        cascade="all, delete-orphan",
    )


class Transfer(Base):
    """
    תיעוד העברות בין ארנקים/משתמשים בתוך מערכת ה-demo.
    """

    __tablename__ = "transfers"

    id = Column(Integer, primary_key=True, index=True)

    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    from_wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    to_wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)

    token_symbol = Column(String(32), nullable=False, default="SLH")
    amount = Column(Float, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    from_user = relationship(
        "User",
        foreign_keys=[from_user_id],
        back_populates="sent_transfers",
    )
    to_user = relationship(
        "User",
        foreign_keys=[to_user_id],
        back_populates="received_transfers",
    )

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


class Order(Base):
    """
    הזמנה דמו (buy/sell) על טוקן SLH
    """

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False, index=True)

    token_symbol = Column(String(32), nullable=False, default="SLH")
    side = Column(String(4), nullable=False)  # "buy" / "sell"
    amount = Column(Float, nullable=False)
    price = Column(Float, nullable=False)

    # זה השדה שה-service משתמש בו: models.Order.is_open.is_(True)
    is_open = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="orders")
    wallet = relationship("Wallet", back_populates="orders")
