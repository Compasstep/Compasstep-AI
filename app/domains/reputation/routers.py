# app/domains/reputation/routers.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_async_db
from app.domains.reputation.schemas import YoutubeReputationRequest, ErrorResponse
from app.domains.reputation.service import YoutubeReputationServiceAsync

router = APIRouter(prefix="/ai/user/analyze", tags=["Reputation / YouTube"])

def get_service():
    return YoutubeReputationServiceAsync()

@router.post("/youtube", response_model=dict, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
async def analyze_youtube_reputation(
    body: YoutubeReputationRequest,
    svc: YoutubeReputationServiceAsync = Depends(get_service),
    db: AsyncSession = Depends(get_async_db),
):
    if not body.songTitle or not body.artist:
        raise HTTPException(status_code=400, detail={"code": "400", "message": "필수 입력 항목이 누락되었습니다.", "result": None})

    # ✅ user_id 처리 추가
    user_id = body.userId or 1

    result = await svc.analyze_youtube_reputation(body.songTitle, body.artist, db, user_id)
    if result is None:
        raise HTTPException(status_code=404, detail={"code": "404", "message": "해당 곡의 유튜브 영상을 찾을 수 없습니다.", "result": None})

    summary_block, review_block = result
    return {"code": "200", "message": "유튜브 댓글 평판 분석에 성공했습니다.", "result": {"summary": summary_block, "reviews": review_block}}
