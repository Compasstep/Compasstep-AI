from sqlalchemy import Column, String, Integer, BigInteger, ForeignKey
from app.db.models.base import Base, TimestampMixin

class GuestComment(Base, TimestampMixin):
    __tablename__ = "guest_comments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    post_id = Column(BigInteger, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    rate = Column(Integer, nullable=False)
    comment = Column(String(255), nullable=False)
