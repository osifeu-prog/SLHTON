from typing import List

from sqlalchemy.orm import Session

from .. import models


def create_order(
    db: Session,
    user: models.User,
    side: str,
    token_symbol: str,
    amount: float,
    price: float,
) -> models.Order:
    side = side.lower()
    if side not in {"buy", "sell"}:
        raise ValueError("side must be 'buy' or 'sell'")

    order = models.Order(
        user_id=user.id,
        side=side,
        token_symbol=token_symbol,
        amount=amount,
        price=price,
        is_open=True,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def list_open_orders(db: Session) -> List[models.Order]:
    return (
        db.query(models.Order)
        .filter(models.Order.is_open.is_(True))
        .order_by(models.Order.created_at.desc())
        .all()
    )
