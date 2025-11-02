# app/domains/peer_reputation/service.py
import asyncio
import os
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.ml.sentiment.keywords import extract_keywords_mixed
from app.ml.sentiment.infer import SentimentModel
from app.db.repository.peer_repository import PeerReputationRepository

load_dotenv()
logger = get_logger("peer_reputation_service")


class PeerReputationServiceAsync:
    """🧠 지인 평판 분석 서비스"""

    def __init__(self):
        self.model = SentimentModel(os.getenv("SENTIMENT_MODEL_PATH"))
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.repo = PeerReputationRepository()

    # ------------------------------------------------------------------
    async def run_sentiment_inference(self, comments: List[str]) -> List[Dict]:
        loop = asyncio.get_running_loop()
        def _predict():
            return self.model.predict_batch(comments)
        return await loop.run_in_executor(self.executor, _predict)

    async def aggregate_summary(self, inference_results: List[Dict]) -> Tuple[Dict[str, float], Dict[str, float]]:
        sentiment_acc = {"positive": 0.0, "negative": 0.0, "neutral": 0.0}
        emotion_acc: Dict[str, float] = {}
        n = len(inference_results)

        for r in inference_results:
            for k in sentiment_acc:
                sentiment_acc[k] += r["polarity"][k]
            for emo, prob in r["emotions"].items():
                emotion_acc[emo] = emotion_acc.get(emo, 0.0) + prob

        if n == 0:
            return {"positive": 0, "negative": 0, "neutral": 0}, {}

        share_summary = {k: round(v / n, 4) for k, v in sentiment_acc.items()}
        share_details = {emo: round(total / n, 4) for emo, total in emotion_acc.items()}
        return share_summary, share_details

    async def extract_keywords_async(self, texts: List[str]) -> List[str]:
        loop = asyncio.get_running_loop()
        def _extract():
            return extract_keywords_mixed(texts)
        return await loop.run_in_executor(self.executor, _extract)

    # ------------------------------------------------------------------
    async def analyze_peer_reputation(self, post_id: int, db: AsyncSession):
        """메인 분석 로직"""
        # 1️⃣ 댓글 가져오기
        raw_comments = await self.repo.get_guest_comments(db, post_id)
        if not raw_comments:
            return None

        texts = [c["text"] for c in raw_comments]

        # 2️⃣ 모델 추론
        preds = await self.run_sentiment_inference(texts)

        # 3️⃣ 요약 및 키워드
        share_summary, share_details = await self.aggregate_summary(preds)
        keywords = await self.extract_keywords_async(texts)
        top_emotions = sorted(share_details.items(), key=lambda x: x[1], reverse=True)[:10]

        # 4️⃣ DB 업데이트 (repository 사용)
        now = await self.repo.update_post_summary(db, post_id, share_summary, share_details, keywords)

        # 5️⃣ 결과 payload 구성
        payload = {
            "postId": post_id,
            "analyzedAt": now.isoformat(),
            "summary": share_summary,
            "top_emotions": top_emotions,
            "keywords": keywords,
            "counts": {"totalComments": len(raw_comments)},
            "meta": {
                "model": os.getenv("SENTIMENT_MODEL_PATH", "dummy"),
                "mappingVersion": "L1_id_map.json",
                "domain": "peer_reputation",
            },
        }

        # ✅ 추후 큐 전송 구조 준비 (주석)
        # from app.core.queue import RabbitMQPublisher
        # publisher = RabbitMQPublisher()
        # await publisher.publish("peer_analysis_queue", payload)

        logger.info(f"[PeerReputation] ✅ Analysis completed for post_id={post_id}")
        return {
            "postId": post_id,
            "share_summary": share_summary,
            "share_details": share_details,
            "keywords": keywords,
        }
