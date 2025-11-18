#app/domains/lyrics/reputation/service

from app.s3.service import S3Service
from app.ml.sentiment.infer import SentimentModel
from app.core.logger import get_logger

logger = get_logger("app.domain.lyrics.reputation.service")

class LyricsReputationService:
    def __init__(self, model):
        self.s3 = S3Service()
        self.sentiment_model = model

    async def analyze_lyrics(self, object_key: str):
        """
        S3에서 가사 불러오기 → 라인별 감정 2개 추출
        반환 형식:
        {
            "analysisResult": [
                {"part": "가사 한 줄", "emotions": ["joy", "sweetness"]},
                ...
            ]
        }
        """
        logger.info("🎵 S3 가사 로딩 시작 - key=%s", object_key)

        lyrics = await self.s3.get_lyrics_from_s3(object_key)
        lines = [line.strip() for line in lyrics.split("\n") if line.strip()]
        logger.info("✅ 가사 로딩 완료 - 총 %d lines", len(lines))

        preds = self.sentiment_model.predict_batch(lines)

        result = []
        for line, pred in zip(lines, preds):
            emotions = pred["emotions"]
            top2 = sorted(emotions.items(), key=lambda x: x[1], reverse=True)[:2]
            emotion_labels = [e for e, _ in top2]

            result.append({
                "part": line,
                "emotions": emotion_labels
            })

        logger.info("✅ 감정 분석 완료 - %d lines", len(result))
        return {"analysisResult": result}
