from sqlalchemy import Column, String, Boolean, BigInteger, Float
from app.db.models.base import Base, TimestampMixin

class AIModel(Base, TimestampMixin):
    __tablename__ = "ai_model"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    accuracy = Column(Float, nullable=False)       # ← added to match schema.sql
    f1_macro_score = Column(Float, nullable=False)
    f1_micro_score = Column(Float, nullable=False)
    is_active = Column(Boolean, nullable=False)
    save_path = Column(String(255), nullable=False)
