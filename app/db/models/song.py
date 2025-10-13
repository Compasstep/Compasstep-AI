from sqlalchemy import Column, String, BigInteger, ForeignKey
from app.db.models.base import Base, TimestampMixin

class Song(Base, TimestampMixin):
    __tablename__ = "song"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    s3_file_key = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
