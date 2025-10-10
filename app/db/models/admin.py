from sqlalchemy import Column, String, Boolean, BigInteger, CheckConstraint, text
from app.db.models.base import Base, TimestampMixin

ROLE_CHECK = CheckConstraint(
    "role IN ('ROOT','GENERAL','DELETED')",
    name="ck_admin_role"
)

class Admin(Base, TimestampMixin):
    __tablename__ = "admin"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=True)
    name = Column(String(255), nullable=True)
    password = Column(String(255), nullable=True)
    role = Column(String(255), nullable=True)

    is_deleted = Column(Boolean, nullable=False, server_default=text("false"))
    temp_pwd = Column(Boolean, nullable=False, server_default=text("false"))

    __table_args__ = (ROLE_CHECK,)
