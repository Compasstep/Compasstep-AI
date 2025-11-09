# app/db/repository/youttube_reputation_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Dict, List
from app.db.models.reputation_analysis import ReputationAnalysis
from app.core.logger import get_logger

logger = get_logger("app.db.repository.youttube_reputation_repo")


class YoutubeReputationRepository:
    """유튜브 평판 분석 결과 저장용 Repository"""

    @staticmethod
    async def save_analysis(
        db: AsyncSession,
        user_id: int,
        song_title: str,
        artist_name: str,
        sentiment_summary: Dict[str, float],
        emotion_details: Dict[str, float],
        keywords: List[str],
        now: datetime
    ) -> int:
        """평판 분석 결과 저장"""
        new_record = ReputationAnalysis(
            user_id=user_id,
            song_title=song_title,
            artist_name=artist_name,
            sentiment_summary=sentiment_summary,
            emotion_details=emotion_details,
            keywords=keywords,
            created_at=now,
            updated_at=now,
        )

        db.add(new_record)
        await db.commit()
        await db.refresh(new_record)
        logger.info(f"✅ 평판 분석 저장 완료: reputation_analysis id={new_record.id}")
        return new_record.id
