from sqlalchemy import Column, Text, Boolean, BigInteger, Float, DateTime, CHAR, Computed
from sqlalchemy.dialects.postgresql import JSONB
from app.db.models.base import Base, TimestampMixin

class RetrainingData(Base, TimestampMixin):
    __tablename__ = "retraining_data"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    comment_text = Column(Text, nullable=False)
    comment_hash = Column( # ✅ 정규화(lower + 공백압축 + trim) 후 MD5 → 32자 해시
        CHAR(32),
        Computed(
            "md5(lower(trim(regexp_replace(comment_text, '\\s+', ' ', 'g'))))",
            persisted=True  # STORED
        ),
        nullable=False
    )

    prediction = Column(JSONB)
    confidence = Column(Float)
    is_learned = Column(Boolean, default=False)
    is_reviewed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
