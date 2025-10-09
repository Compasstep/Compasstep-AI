# app/db/models/user.py
from sqlalchemy import (
    Column, String, Boolean, BigInteger, CheckConstraint, text
)
from app.db.models.base import Base, TimestampMixin

# 스키마는 VARCHAR + CHECK 제약(ENUM 아님) → String + CheckConstraint 로 구현
STATUS_CHECK = CheckConstraint(
    "status IN ('NORMAL','SUSPENDED','BLOCKED','DELETED')",
    name="ck_users_status"
)

class User(Base, TimestampMixin):
    __tablename__ = "users"  # 스키마와 동일

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    nickname = Column(String(255), nullable=False)
    s3file_image = Column(String(255), nullable=True)
    status = Column(String(255), nullable=False, server_default=text("'NORMAL'"))
    status_reason = Column(String(255), nullable=True)
    is_deleted = Column(Boolean, nullable=False, server_default=text("false"))

    __table_args__ = (STATUS_CHECK,)
