# app/models/chat.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, BigInteger
from app.db.models.base import Base, TimestampMixin

class Chat(Base, TimestampMixin):
    __tablename__ = "chat"

    chat_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False)
    content = Column(String, nullable=False)
    is_guardrailed = Column(Boolean, default=False)
