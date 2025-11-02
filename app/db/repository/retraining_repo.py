from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from typing import Dict, List
from app.db.models.retraining_data import RetrainingData
from app.core.logger import get_logger

logger = get_logger("retraining_repo")


class RetrainingRepository:
    """재학습 데이터 저장용 Repository"""

    @staticmethod
    async def save_retraining_data(
        db: AsyncSession,
        reviews: List[Dict],
        now: datetime,
        conf_threshold: float = 0.5,
    ) -> int:
        """confidence 낮은 데이터만 저장 (중복 자동 무시)"""
        retrain_rows = []
        for review in reviews:
            emotions = review["prediction"]["emotions"]
            confidence = float(review["prediction"]["confidence"])
            comment_text = review["commentText"]

            if confidence < conf_threshold:
                retrain_rows.append({
                    "comment_text": comment_text,
                    "prediction": emotions,
                    "confidence": confidence,
                    "is_learned": False,
                    "is_reviewed": False,
                    "created_at": now,
                    "updated_at": now,
                })

        if not retrain_rows:
            logger.info(f"✅ 재학습 데이터 없음 (모든 confidence ≥ {conf_threshold})")
            return 0

        try:
            stmt = insert(RetrainingData.__table__).values(retrain_rows)\
                .on_conflict_do_nothing(index_elements=["comment_hash"])
            await db.execute(stmt)
            await db.commit()
            logger.info(f"✅ 재학습 데이터 {len(retrain_rows)}건 저장 완료 (중복 자동 무시)")
            return len(retrain_rows)
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"❌ 재학습 데이터 저장 중 오류 발생: {e}")
            return 0
