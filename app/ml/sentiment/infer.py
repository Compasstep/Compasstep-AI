from typing import List, Dict
import random

class SentimentModel:
    """
    Dummy SentimentModel
    실제 XLM-RoBERTa 모델 대신 더미 예측을 수행.
    """

    def __init__(self):
        print("[SentimentModel] Dummy model initialized.")

    def predict_batch(self, comments: List[str]) -> List[Dict]:
        """
        입력된 댓글 리스트에 대해 임의의 감정 확률 분포를 반환
        """
        results = []
        emotions = ["joy", "admiration", "anger", "sadness", "love", "confusion"]
        for text in comments:
            # 무작위 확률값 생성
            emo_probs = {e: round(random.uniform(0, 1), 2) for e in emotions}
            # 확률 정규화
            s = sum(emo_probs.values())
            emo_probs = {k: round(v / s, 3) for k, v in emo_probs.items()}

            polarity = {
                "positive": round(random.uniform(0.6, 0.9), 2),
                "negative": round(random.uniform(0.05, 0.2), 2),
                "neutral": round(random.uniform(0.05, 0.2), 2),
            }

            results.append({"emotions": emo_probs, "polarity": polarity})
        return results
