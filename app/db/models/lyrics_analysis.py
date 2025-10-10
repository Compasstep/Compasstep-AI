from sqlalchemy import Column, BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from app.db.models.base import Base, TimestampMixin

class LyricsAnalysis(Base, TimestampMixin):
    __tablename__ = "lyrics_analysis"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    lyrics_id = Column(BigInteger, ForeignKey("lyrics.id", ondelete="CASCADE"), nullable=False, unique=True)
    analysis_result = Column(JSONB, nullable=False)

    __table_args__ = (
        UniqueConstraint("lyrics_id", name="uq_lyrics_analysis_lyrics_id"),
    )
