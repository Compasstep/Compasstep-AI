# app/domains/lyrics/service.py
from typing import List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.lyrics.reputation.service import LyricsReputationService
from app.domains.lyrics.coaching.service import generate_vocal_coaching
from app.db.repository.lyrics_repository import LyricsRepository
from app.core.logger import get_logger

logger = get_logger("app.domains.lyrics.service")

class LyricsService:
    def __init__(self):
        self.reputation = LyricsReputationService()

    async def analyze_and_save(self, db: AsyncSession, lyrics_id: int) -> Dict[str, Any]:
        """
        1) lyrics_id -> S3 key 조회 (LyricsRepository.get_s3_path_by_id)
        2) reputation.analyze_lyrics(s3_key) 호출 -> {"analysisResult": [ {"part", "emotions"}, ... ]}
        3) 인덱스 추가 (index를 부여)
        4) generate_vocal_coaching(indexed_list) 호출 -> {"coachingList": [...]}
        5) index 기준으로 merge -> final_analysis: {"analysisData": [ {"part","emotions","coaching"}, ... ]}
        6) DB 저장 (LyricsRepository.save_analysis)
        7) return final_result (for API)
        """

        logger.info(f"통합 가사 분석 시작 (lyrics_id={lyrics_id})")

        # 1) DB에서 S3 경로 조회
        s3_key = await LyricsRepository.get_s3_path_by_id(db, lyrics_id)

        # 2) reputation 분석(가사 다운로드 포함)
        rep_result = await self.reputation.analyze_lyrics(s3_key)
        if not rep_result or "analysisResult" not in rep_result:
            raise ValueError("감정 분석 결과가 없습니다.")

        analysis_list = rep_result["analysisResult"]
        if not isinstance(analysis_list, list):
            raise ValueError("감정 분석 결과 형식이 올바르지 않습니다.")

        # 3) 인덱스 추가 (index는 0부터)
        indexed: List[Dict[str, Any]] = []
        for i, item in enumerate(analysis_list):
            indexed.append({
                "index": i,
                "part": item.get("part"),
                "emotions": item.get("emotions", [])
            })

        # 4) LLM 코칭 (coachingList 받기)
        try:
            coaching_out = generate_vocal_coaching(indexed)
        except Exception as e:
            # LLM 파싱 실패 등
            logger.error("보컬 코칭 생성 실패: %s", e)
            raise

        coaching_list = coaching_out.get("coachingList", [])

        # 5) Merge: coaching_list -> dict(index->coaching)
        coaching_map = {entry["index"]: entry["coaching"] for entry in coaching_list}

        analysis_data = []
        for item in indexed:
            idx = item["index"]
            part = item["part"]
            emotions = item["emotions"]
            coaching_text = coaching_map.get(idx, "")  # 없으면 빈문자열
            analysis_data.append({
                "part": part,
                "emotions": emotions,
                "coaching": coaching_text
            })

        final_result = {
            "analysisData": analysis_data
        }

        # 6) DB 저장 (lyrics_analysis 분석 테이블)
        await LyricsRepository.save_analysis(db, lyrics_id, final_result)

        logger.info(f"전체 저장 완료 (lyrics_id={lyrics_id})")
        return final_result
