# app/services/users.py
from sqlalchemy.orm import Session

from .. import models


def get_or_create_user(
    db: Session,
    telegram_id: int,
    username: str | None,
    first_name: str | None,
    last_name: str | None,
) -> models.User:
    user = db.query(models.User).filter(models.User.telegram_id == telegram_id).first()

    if user is None:
        user = models.User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    # עדכון פרטים בסיסי אם השתנו
    changed = False
    if username is not None and user.username != username:
        user.username = username
        changed = True
    if first_name is not None and user.first_name != first_name:
        user.first_name = first_name
        changed = True
    if last_name is not None and user.last_name != last_name:
        user.last_name = last_name
        changed = True

    if changed:
        db.commit()
        db.refresh(user)

    return user


def get_user_by_telegram_id(db: Session, telegram_id: int) -> models.User | None:
    return db.query(models.User).filter(models.User.telegram_id == telegram_id).first()


def get_user_by_username(db: Session, username: str) -> models.User | None:
    # נשווה בלי @ ו-case-sensitive כמו שטלגרם שומר
    clean = username.lstrip("@")
    return db.query(models.User).filter(models.User.username == clean).first()
