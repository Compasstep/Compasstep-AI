from sqlalchemy import Column, String, BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from app.db.models.base import Base, TimestampMixin

class Post(Base, TimestampMixin):
    __tablename__ = "posts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    song_id = Column(BigInteger, ForeignKey("song.id", ondelete="CASCADE"), nullable=False, unique=True)

    keywords = Column(JSONB, nullable=True)
    post_name = Column(String(255), nullable=True)

    share_details = Column(JSONB, nullable=True)
    share_summary = Column(JSONB, nullable=True)

    analyzed = Column(Boolean, nullable=False, server_default=expression.false())

    __table_args__ = (
        UniqueConstraint("song_id", name="uq_posts_song_id"),
    )
