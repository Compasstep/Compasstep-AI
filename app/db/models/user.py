import enum
from sqlalchemy import Column, String, Boolean, DateTime, Text, BigInteger, Enum
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import VARCHAR
from app.db.models.base import Base, TimestampMixin

class UserStatus(str, enum.Enum):
    NORMAL = "NORMAL"
    SUSPENDED = "SUSPENDED"
    BLOCKED = "BLOCKED"

class User(Base, TimestampMixin):
    __tablename__ = "user"

    user_id = Column(BigInteger, primary_key=True, autoincrement=True)
    google_user_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    nickname = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    status = Column(Enum(UserStatus, name="user_status"), nullable=False, default=UserStatus.NORMAL)
    status_reason = Column(Text, nullable=True)
    is_deleted = Column(Boolean, nullable=False, default=False)
    s3_file_key = Column(String(512), nullable=False)