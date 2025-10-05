# app/db/repository/user_repository.py
from datetime import datetime, timedelta, UTC
from typing import Optional

from sqlalchemy import select, update, func
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.db.models.chat import Chat


MAX_REASON_LEN = 255
ALLOWED_STATUSES = {"NORMAL", "SUSPENDED", "BLOCKED", "DELETED"}

def get_user_by_id(db: Session, id: int) -> Optional[User]:
    """특정 user_id로 유저를 조회합니다."""
    return db.get(User, id)

def update_user_status(
    db: Session,
    id: int,
    new_status: str,
    reason: Optional[str] = None,
) -> None:
    """
    유저 상태를 변경합니다.
    - new_status: "NORMAL" | "SUSPENDED" | "BLOCKED" | "DELETED"
    - reason: 정지/차단 사유 (최대 255자)
    트랜잭션 커밋/롤백은 호출자에서 관리합니다.
    """
    status_value = str(new_status).upper()
    if status_value not in ALLOWED_STATUSES:
        raise ValueError(f"Invalid status '{new_status}'. Allowed: {sorted(ALLOWED_STATUSES)}")

    safe_reason = reason.strip()[:MAX_REASON_LEN] if reason else None

    db.execute(
        update(User)
        .where(User.id == id)
        .values(
            status=status_value,
            status_reason=safe_reason,
            updated_at=datetime.now(UTC),
        )
    )
    # 여기서는 commit 하지 않음 (서비스 레이어에서 commit)

def count_guardrails_in_last_hour(db: Session, id: int) -> int:
    """최근 1시간 내 해당 유저의 가드레일 탐지 횟수."""
    one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
    result = db.scalar(
        select(func.count(Chat.id))
        .where(Chat.user_id == id)
        .where(Chat.is_guardrailed.is_(True))
        .where(Chat.created_at >= one_hour_ago)
    )
    return int(result or 0)
