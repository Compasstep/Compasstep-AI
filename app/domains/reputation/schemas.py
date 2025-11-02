from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime


# === Request ===
class YoutubeReputationRequest(BaseModel):
    songTitle: str = Field(..., description="곡 제목")
    artist: str = Field(..., description="가수 이름")
    userId: int | None = None  # 🔹 자바에서 넘기거나 없을 수도 있음


# === Response: Summary ===
class SentimentSummary(BaseModel):
    positive: float
    negative: float
    neutral: float


class ReputationSummaryResult(BaseModel):
    analysisId: int
    songTitle: str
    sentimentSummary: SentimentSummary
    emotionDetails: Dict[str, float]
    keywords: List[str]


class YoutubeReputationSummaryResponse(BaseModel):
    code: str = "200"
    message: str = "유튜브 댓글 평판 분석에 성공했습니다."
    result: ReputationSummaryResult


# === Response: Review Items ===
class PredictionInfo(BaseModel):
    emotions: List[str]
    confidence: float
    probabilities: Dict[str, float]


class ReviewItem(BaseModel):
    yCommentId: str
    commentText: str
    prediction: PredictionInfo
    isReviewed: bool
    createdAt: datetime


class ReviewListResult(BaseModel):
    reviews: List[ReviewItem]


class YoutubeReputationReviewResponse(BaseModel):
    code: str = "200"
    message: str = "AI 분석 검토 대기 목록 조회가 성공했습니다."
    result: ReviewListResult


# === Error Response ===
class ErrorResponse(BaseModel):
    code: str
    message: str
    result: Optional[dict] = None
