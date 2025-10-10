from sqlalchemy import Column, String, Boolean, BigInteger, Float, text
from sqlalchemy.dialects.postgresql import JSONB
from app.db.models.base import Base, TimestampMixin

class RetrainingData(Base, TimestampMixin):
    __tablename__ = "retraining_data"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    comment_text = Column(String(255), nullable=False)
    prediction = Column(JSONB, nullable=False)

    confidence = Column(Float, nullable=False)
    is_learned = Column(Boolean, nullable=False)
    is_reviewed = Column(Boolean, nullable=False, server_default=text("false"))
