# app/db/repository/chat_repository.py
from sqlalchemy.orm import Session
from app.db.models.chat import Chat

def create_chat(db: Session, user_id: int, content: str, is_guardrailed: bool) -> Chat:
    chat = Chat(user_id=user_id, content=content, is_guardrailed=is_guardrailed)
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat