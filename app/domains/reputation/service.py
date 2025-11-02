# app/domains/reputation/service.py
import aiohttp
import asyncio
import os
from datetime import datetime, timezone
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from app.db.models.reputation_analysis import ReputationAnalysis
from app.db.models.retraining_data import RetrainingData

from app.core.logger import get_logger
from app.ml.sentiment.keywords import extract_keywords_mixed
from app.ml.sentiment.infer import SentimentModel

#from app.core.cache import RedisCache


load_dotenv()
logger = get_logger("reputation_service")

CONF_THRESHOLD = 0.5

# ---------------------------------------------------------------------------
# 🧠 메인 서비스 클래스
# ---------------------------------------------------------------------------
class YoutubeReputationServiceAsync:
    def __init__(self):
        self.model = SentimentModel(os.getenv("SENTIMENT_MODEL_PATH"))
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")

    # ----------------------------------------------------------------------
    async def fetch_youtube_video_ids(self, session: aiohttp.ClientSession, query: str, max_candidates: int = 3) -> List[str]:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "id",
            "q": query,
            "key": self.youtube_api_key,
            "type": "video",
            "maxResults": max_candidates,
        }
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            items = data.get("items", [])
            return [item["id"]["videoId"] for item in items if "id" in item and "videoId" in item["id"]]

    # ----------------------------------------------------------------------
    async def fetch_youtube_comments(self, artist: str, song_title: str, max_comments: int = 100) -> List[Dict]:
        query = f"{artist} {song_title}"
        comments = []
        async with aiohttp.ClientSession() as session:
            video_ids = await self.fetch_youtube_video_ids(session, query)
            if not video_ids:
                logger.warning(f"No videos found for {query}")
                return []

            for video_id in video_ids:
                try:
                    url = "https://www.googleapis.com/youtube/v3/commentThreads"
                    params = {
                        "part": "snippet",
                        "videoId": video_id,
                        "maxResults": 50,
                        "key": self.youtube_api_key,
                        "textFormat": "plainText",
                        "order": "relevance",
                    }
                    tmp_comments = []
                    while True:
                        async with session.get(url, params=params) as resp:
                            data = await resp.json()
                            if "error" in data:
                                break
                            for item in data.get("items", []):
                                snippet = item["snippet"]["topLevelComment"]["snippet"]
                                tmp_comments.append({
                                    "comment_id": item["id"],
                                    "text": snippet["textDisplay"],
                                    "video_id": video_id,
                                    "published_at": datetime.fromisoformat(
                                        snippet["publishedAt"].replace("Z", "+00:00")
                                    ),
                                })
                            if "nextPageToken" in data and len(tmp_comments) < max_comments:
                                params["pageToken"] = data["nextPageToken"]
                            else:
                                break
                    if len(tmp_comments) >= 10:
                        logger.info(f"Selected video: https://www.youtube.com/watch?v={video_id}")
                        comments = tmp_comments[:max_comments]
                        break
                except Exception as e:
                    logger.error(f"Failed to fetch comments for {video_id}: {e}")
                    continue
        return comments

    # ----------------------------------------------------------------------
    async def run_sentiment_inference(self, comments: List[str]) -> List[Dict]:
        loop = asyncio.get_running_loop()

        def _predict():
            return self.model.predict_batch(comments)

        return await loop.run_in_executor(self.executor, _predict)

    # ----------------------------------------------------------------------
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

        sentiment_summary = {k: v / n for k, v in sentiment_acc.items()}
        emotion_details = {emo: total / n for emo, total in emotion_acc.items()}
        return sentiment_summary, emotion_details

    # ----------------------------------------------------------------------
    async def extract_keywords_async(self, texts: List[str]) -> List[str]:
        """한국어 + 영어 혼합 키워드 추출 (비동기 안전)"""
        loop = asyncio.get_event_loop()

        def _extract():
            return extract_keywords_mixed(texts)

        keywords = await loop.run_in_executor(self.executor, _extract)
        return keywords

    # ----------------------------------------------------------------------
    async def build_review_items(self, comments: List[Dict], inference_results: List[Dict]) -> List[Dict]:
        items = []
        for c, pred in zip(comments, inference_results):
            sorted_emotions = sorted(pred["emotions"].items(), key=lambda x: x[1], reverse=True)
            top_labels = [e for e, _ in sorted_emotions[:2]]
            conf = sorted_emotions[0][1] if sorted_emotions else 0.0
            items.append({
                "commentText": c["text"],
                "prediction": {
                    "emotions": top_labels,
                    "confidence": conf,
                    "probabilities": pred["emotions"],
                },
                "isReviewed": False,
                "createdAt": c["published_at"].isoformat().replace("+00:00", "Z"),
            })
        return items

    # ----------------------------------------------------------------------
    async def analyze_youtube_reputation(self, song_title: str, artist: str, db: AsyncSession, user_id: int):
        # 1️⃣ 댓글 수집
        raw_comments = await self.fetch_youtube_comments(artist, song_title)
        if not raw_comments:
            return None

        texts = [c["text"] for c in raw_comments]

        # 2️⃣ 감정 분석
        preds = await self.run_sentiment_inference(texts)

        # 3️⃣ 집계 및 키워드
        sentiment_summary, emotion_details = await self.aggregate_summary(preds)
        keywords = await self.extract_keywords_async(texts)
        reviews = await self.build_review_items(raw_comments, preds)
        top_emotions = sorted(emotion_details.items(), key=lambda x: x[1], reverse=True)[:10]

        now = datetime.now(timezone.utc)
        video_id = raw_comments[0].get("video_id", "unknown")

        # ✅ reputation_analysis 저장
        new_record = ReputationAnalysis(
            user_id=user_id,
            song_title=song_title,
            artist_name=artist,
            sentiment_summary=sentiment_summary,
            emotion_details=emotion_details,
            keywords=keywords,
            created_at=now,
            updated_at=now
        )

        db.add(new_record)
        await db.commit()
        await db.refresh(new_record)
        logger.info(f"✅ 평판 분석 결과 저장 완료: reputation_analysis id={new_record.id}")

        # ✅ retraining_data 저장
        retrain_rows = []
        for review in reviews:
            emotions = review["prediction"]["emotions"]  # 상위 2개 감정 레이블
            confidence = float(review["prediction"]["confidence"])
            comment_text = review["commentText"]

            if confidence < CONF_THRESHOLD:
                # 🔁 ORM 인스턴스 말고 "딕셔너리"로 바로 적재
                retrain_rows.append({
                    "comment_text": comment_text,
                    "prediction": emotions,  # ["admiration","confusion"]
                    "confidence": confidence,
                    "is_learned": False,
                    "is_reviewed": False,
                    "created_at": now,
                    "updated_at": now,
                    # ⚠️ comment_hash 는 DB가 자동 생성한다. 여기서 넣지 말 것!
                })

        if retrain_rows:
            try:
                stmt = insert(RetrainingData.__table__).values(retrain_rows) \
                    .on_conflict_do_nothing(index_elements=["comment_hash"])  # ✅ 해시 기준 중복 무시

                await db.execute(stmt)
                await db.commit()
                logger.info(f"✅ 재학습용 데이터 {len(retrain_rows)}건 저장 시도 완료 (중복은 자동 무시, threshold={CONF_THRESHOLD})")

            except SQLAlchemyError as e:
                await db.rollback()
                logger.error(f"❌ 재학습 데이터 저장 중 오류 발생: {e}")
        else:
            logger.info(f"✅ 재학습 데이터 없음 (모든 confidence ≥ {CONF_THRESHOLD})")

        # 4️⃣ Redis 저장용 payload
        payload = {
            "videoId": video_id,
            "songTitle": song_title,
            "artist": artist,
            "analyzedAt": now,
            "summary": sentiment_summary,
            "top_emotions": top_emotions,
            "keywords": keywords,
            "counts": {"totalComments": len(raw_comments), "sampled": len(texts)},
            "meta": {
                "model": os.getenv("SENTIMENT_MODEL_PATH", "dummy"),
                "mappingVersion": "L1_id_map.json",
                "polarityRule": "per-comment majority among top-k emotions (k=6)",
            },
        }

        # ✅ Redis 캐싱
        #cache = RedisCache()
        #cache.set_json(f"rep:{video_id}", payload)

        summary_block = {
            "songTitle": song_title,
            "sentimentSummary": sentiment_summary,
            "emotionDetails": emotion_details,
            "keywords": keywords,
        }

        return summary_block, reviews
