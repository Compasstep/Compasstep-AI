import aiohttp
import asyncio
import os
from datetime import datetime
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

from app.core.logger import get_logger
from app.ml.sentiment.infer import SentimentModel

load_dotenv()
logger = get_logger("reputation_service")


class YoutubeReputationServiceAsync:
    def __init__(self):
        self.model = SentimentModel()
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")

    # ----------------------------------------------------------------------
    async def fetch_youtube_video_ids(self, session: aiohttp.ClientSession, query: str, max_candidates: int = 3) -> List[str]:
        """
        아티스트+곡명으로 YouTube 영상 여러 개 검색 (최대 max_candidates개)
        """
        search_url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "id",
            "q": query,
            "key": self.youtube_api_key,
            "type": "video",
            "maxResults": max_candidates,
        }
        async with session.get(search_url, params=params) as resp:
            data = await resp.json()
            items = data.get("items", [])
            video_ids = [item["id"]["videoId"] for item in items if "id" in item and "videoId" in item["id"]]
            return video_ids

    # ----------------------------------------------------------------------
    async def fetch_youtube_comments(self, artist: str, song_title: str, max_comments: int = 100) -> List[Dict]:
        """
        유튜브 댓글 비동기 수집
        - 최대 3개의 영상 후보를 검색하고
        - 첫 번째로 댓글을 성공적으로 수집한 영상에 대해 분석 진행
        """
        query = f"{artist} {song_title}"
        comments = []

        async with aiohttp.ClientSession() as session:
            # 1️⃣ 여러 후보 영상 검색
            video_ids = await self.fetch_youtube_video_ids(session, query)
            if not video_ids:
                logger.warning(f"[YouTube] No video found for {query}")
                return []

            logger.info(f"[YouTube] Candidate videos: {', '.join(video_ids)}")

            # 2️⃣ 각 영상에 대해 댓글 시도
            for video_id in video_ids:
                try:
                    url = "https://www.googleapis.com/youtube/v3/commentThreads"
                    params = {
                        "part": "snippet",
                        "videoId": video_id,
                        "maxResults": 50,
                        "key": self.youtube_api_key,
                        "textFormat": "plainText",
                        "order": "relevance",  # 인기순 정렬
                    }

                    tmp_comments = []
                    while True:
                        async with session.get(url, params=params) as resp:
                            data = await resp.json()

                            # API 요청 실패 시 중단
                            if "error" in data:
                                logger.warning(f"[YouTube] Error fetching comments for {video_id}: {data['error']}")
                                break

                            items = data.get("items", [])
                            for item in items:
                                try:
                                    snippet = item["snippet"]["topLevelComment"]["snippet"]
                                    tmp_comments.append({
                                        "comment_id": item["id"],
                                        "text": snippet["textDisplay"],
                                        "published_at": datetime.fromisoformat(
                                            snippet["publishedAt"].replace("Z", "+00:00")
                                        ),
                                    })
                                except Exception:
                                    continue

                            # 다음 페이지 처리
                            if "nextPageToken" in data and len(tmp_comments) < max_comments:
                                params["pageToken"] = data["nextPageToken"]
                            else:
                                break

                    # 3️⃣ 댓글이 일정 수 이상 있으면 이 영상 선택
                    if len(tmp_comments) >= 10:
                        logger.info(f"[YouTube] ✅ Selected video: https://www.youtube.com/watch?v={video_id}")
                        comments = tmp_comments[:max_comments]
                        break
                    else:
                        logger.info(f"[YouTube] ⚠️ Video {video_id} has too few comments ({len(tmp_comments)}). Trying next...")

                except Exception as e:
                    logger.error(f"[YouTube] Failed to fetch comments for {video_id}: {e}")
                    continue

        if not comments:
            logger.warning(f"[YouTube] ❌ No suitable videos with enough comments found for '{query}'.")

        return comments[:max_comments]

    # ----------------------------------------------------------------------
    async def run_sentiment_inference(self, comments: List[str]) -> List[Dict]:
        loop = asyncio.get_event_loop()

        def _predict():
            logger.info(f"Running sentiment inference on {len(comments)} comments...")
            return self.model.predict_batch(comments)

        preds = await loop.run_in_executor(self.executor, _predict)
        return preds

    # ----------------------------------------------------------------------
    async def extract_keywords(self, comments: List[str]) -> List[str]:
        await asyncio.sleep(0)
        return ["달달하다", "음색", "중독성", "새벽감성", "편안한"]

    # ----------------------------------------------------------------------
    async def aggregate_summary(self, inference_results: List[Dict]) -> Tuple[Dict[str, float], Dict[str, float]]:
        sentiment_acc = {"positive": 0.0, "negative": 0.0, "neutral": 0.0}
        emotion_acc: Dict[str, float] = {}
        n = len(inference_results)

        for r in inference_results:
            pol = r["polarity"]
            sentiment_acc["positive"] += pol["positive"]
            sentiment_acc["negative"] += pol["negative"]
            sentiment_acc["neutral"] += pol["neutral"]
            for emo, prob in r["emotions"].items():
                emotion_acc[emo] = emotion_acc.get(emo, 0.0) + prob

        if n == 0:
            return {"positive": 0, "negative": 0, "neutral": 0}, {}

        sentiment_summary = {k: v / n for k, v in sentiment_acc.items()}
        emotion_details = {emo: total / n for emo, total in emotion_acc.items()}
        return sentiment_summary, emotion_details

    # ----------------------------------------------------------------------
    async def build_review_items(self, comments: List[Dict], inference_results: List[Dict]) -> List[Dict]:
        items = []
        for c, pred in zip(comments, inference_results):
            sorted_emotions = sorted(pred["emotions"].items(), key=lambda x: x[1], reverse=True)
            top_labels = [e for e, _ in sorted_emotions[:2]]
            top_conf = sorted_emotions[0][1] if sorted_emotions else 0.0

            items.append({
                "yCommentId": c["comment_id"],
                "commentText": c["text"],
                "prediction": {
                    "emotions": top_labels,
                    "confidence": top_conf,
                    "probabilities": pred["emotions"]
                },
                "isReviewed": False,
                "createdAt": c["published_at"].isoformat() + "Z",
            })
        return items

    # ----------------------------------------------------------------------
    async def analyze_youtube_reputation(self, song_title: str, artist: str):
        raw_comments = await self.fetch_youtube_comments(artist, song_title)
        if not raw_comments:
            return None

        texts = [c["text"] for c in raw_comments]

        preds = await self.run_sentiment_inference(texts)
        sentiment_summary, emotion_details = await self.aggregate_summary(preds)
        keywords = await self.extract_keywords(texts)
        reviews = await self.build_review_items(raw_comments, preds)

        summary_block = {
            "analysisId": 12,
            "songTitle": song_title,
            "sentimentSummary": sentiment_summary,
            "emotionDetails": emotion_details,
            "keywords": keywords,
        }

        return summary_block, reviews
