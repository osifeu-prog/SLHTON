from sqlalchemy.orm import Session

from .. import models


def get_or_create_user(
    db: Session,
    *,
    telegram_id: int,
    username: str | None,
    first_name: str | None,
) -> models.User:
    """
    מאחזר משתמש לפי telegram_id, ואם לא קיים – יוצר אחד חדש.
    מעדכן username / first_name כשצריך.
    """
    user = db.query(models.User).filter(models.User.telegram_id == telegram_id).first()
    if user:
        updated = False

        if username and user.username != username:
            user.username = username
            updated = True

        if first_name and user.first_name != first_name:
            user.first_name = first_name
            updated = True

        if updated:
            db.commit()
            db.refresh(user)

        return user

    user = models.User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_telegram_id(db: Session, telegram_id: int) -> models.User | None:
    return db.query(models.User).filter(models.User.telegram_id == telegram_id).first()


def get_user_by_username(db: Session, username: str) -> models.User | None:
    return (
        db.query(models.User)
        .filter(models.User.username == username)
        .first()
    )
