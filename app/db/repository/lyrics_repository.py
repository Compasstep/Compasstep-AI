# app/db/repository/lyrics_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.db.models.lyrics import Lyrics
from app.db.models.lyrics_analysis import LyricsAnalysis
from app.core.logger import get_logger

logger = get_logger("app/db/repository/lyrics_repository")

class LyricsRepository:

    # 1) DB에서 S3 경로 가져오기 (lyrics/ 부터 추출)
    @staticmethod
    async def get_s3_path_by_id(db: AsyncSession, lyrics_id: int) -> str:
        query = select(Lyrics).where(Lyrics.id == lyrics_id)
        result = await db.execute(query)
        record = result.scalar()

        if not record:
            raise ValueError(f"lyrics_id={lyrics_id} 데이터 없음")

        raw_path = record.s3_lyrics  # 예: s3://bucket/lyrics/bamyangang.txt

        # "lyrics/" 이후만 추출
        if "lyrics/" in raw_path:
            s3_key = "lyrics/" + raw_path.split("lyrics/", 1)[1]
        else:
            s3_key = raw_path  # fallback

        logger.info(f"lyrics 조회 완료 id={lyrics_id}, s3_key={s3_key}")
        return s3_key

    # 2) 분석 결과 저장 (Upsert)
    @staticmethod
    async def save_analysis(db: AsyncSession, lyrics_id: int, analysis_result: dict) -> int:
        now = datetime.now()

        # 1) 기존 분석 여부 조회
        query = select(LyricsAnalysis).where(LyricsAnalysis.lyrics_id == lyrics_id)
        result = await db.execute(query)
        record = result.scalar()

        # 2) 없으면 → INSERT
        if not record:
            new_record = LyricsAnalysis(
                lyrics_id=lyrics_id,
                analysis_result=analysis_result,
                created_at=now,
                updated_at=now
            )
            db.add(new_record)
            await db.commit()
            await db.refresh(new_record)

            logger.info(f"가사 분석 INSERT 완료 (lyrics_id={lyrics_id}) → analysis_id={new_record.id}")
            return new_record.id

        # 3) 있으면 → UPDATE
        record.analysis_result = analysis_result
        record.updated_at = now

        await db.commit()
        await db.refresh(record)

        logger.info(f"가사 분석 UPDATE 완료 (lyrics_id={lyrics_id}) → analysis_id={record.id}")
        return record.id
