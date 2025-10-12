from sqlalchemy import Column, String, BigInteger
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from app.db.models.base import Base, TimestampMixin

class ReputationAnalysis(Base, TimestampMixin):
    __tablename__ = "reputation_analysis"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    artist_name = Column(String(255), nullable=False)
    song_title = Column(String(255), nullable=False)

    emotion_details = Column(JSONB, nullable=False)
    keywords = Column(JSONB, nullable=False)
    sentiment_summary = Column(JSONB, nullable=False)
