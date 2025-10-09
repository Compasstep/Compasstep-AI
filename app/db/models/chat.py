# app/db/models/chat.py
from sqlalchemy import Column, String, Boolean, ForeignKey, BigInteger, text
from app.db.models.base import Base, TimestampMixin

class Chat(Base, TimestampMixin):
    __tablename__ = "chats"  # 스키마와 동일

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 스키마는 varchar(255) NOT NULL
    content = Column(String(255), nullable=False)
    # 스키마는 boolean NOT NULL → 서버 기본값 false
    is_guardrailed = Column(Boolean, nullable=False, server_default=text("false"))
