from datetime import datetime, timedelta, UTC
from sqlalchemy.orm import Session
from sqlalchemy import select, update, func

from app.db.models.user import User
from app.db.models.chat import Chat


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """user_id로 유저 조회"""
    return db.execute(
        select(User).where(User.user_id == user_id)
    ).scalar_one_or_none()


def update_user_status(db: Session, user_id: int, new_status: str, reason: str | None = None) -> None:
    """유저 상태 변경 (예: SUSPENDED, BLOCKED)"""
    db.execute(
        update(User)
        .where(User.user_id == user_id)
        .values(status=new_status, status_reason=reason)
    )
    db.commit()


def count_guardrails_in_last_hour(db: Session, user_id: int) -> int:
    """최근 1시간 내 해당 유저의 가드레일 위반 횟수"""
    one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
    return db.execute(
        select(func.count(Chat.chat_id))
        .where(Chat.user_id == user_id)
        .where(Chat.is_guardrailed == True)
        .where(Chat.created_at >= one_hour_ago)
    ).scalar()
