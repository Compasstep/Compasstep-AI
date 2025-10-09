# app/db/repository/chat_repository.py
from sqlalchemy.orm import Session
from app.db.models.chat import Chat
from app.db.models.user import User
from sqlalchemy.exc import IntegrityError

MAX_LEN = 255

def create_chat(db: Session, user_id: int, content: str, is_guardrailed: bool = False) -> Chat:
    """
    새 채팅 데이터를 DB에 저장하고 반환합니다.
    트랜잭션(커밋/롤백)은 호출자가 관리합니다.
    """
    # 존재하는 유저인지 확인
    user = db.get(User, user_id)
    if not user:
        raise ValueError(f"User with ID {user_id} does not exist")

    if content is None or not content.strip():
        raise ValueError("content must not be empty")
    safe_content = content.strip()[:MAX_LEN]

    chat = Chat(
        user_id=user_id,
        content=safe_content,
        is_guardrailed=bool(is_guardrailed),
    )

    db.add(chat)
    try:
        db.flush()  # PK 할당 및 제약조건 조기 검증
    except IntegrityError as e:
        db.rollback()
        raise RuntimeError(f"DB Integrity Error: {e}") from e

    db.refresh(chat)  # 방금 flush로 반영된 값 가져오기
    return chat
