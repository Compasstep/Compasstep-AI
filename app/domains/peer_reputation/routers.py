# app/domains/peer_reputation/routers.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_async_db
from app.domains.peer_reputation.schemas import PeerReputationRequest, ErrorResponse
from app.domains.peer_reputation.service import PeerReputationServiceAsync
from app.core.logger import setup_logging, get_logger


router = APIRouter(prefix="/ai/user/analyze", tags=["Reputation / Peer"])

# ----------------------------------------------------------------------
# 🧠 서비스 의존성 주입
# ----------------------------------------------------------------------
def get_service():
    return PeerReputationServiceAsync()


# ----------------------------------------------------------------------
# 🧩 API 엔드포인트
# ----------------------------------------------------------------------
@router.post(
    "/peer",
    response_model=dict,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse}
    }
)
async def analyze_peer_reputation(
    body: PeerReputationRequest,
    svc: PeerReputationServiceAsync = Depends(get_service),
    db: AsyncSession = Depends(get_async_db),
):
    """
    POST /ai/user/analyze/peer
    요청 본문: { "postId": 34 }

    guest_comment 테이블에서 댓글 가져와 모델 분석 후
    post 테이블에 share_summary, share_details, keywords 업데이트.
    """
    setup_logging()
    logger = get_logger("라우터")
    logger.debug(f"postId={body.postId}")

    if not body.postId:
        raise HTTPException(
            status_code=400,
            detail={"code": "400", "message": "postId는 필수 입력 항목입니다.", "result": None}
        )

    result = await svc.analyze_peer_reputation(body.postId, db)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "404", "message": "해당 post에 대한 댓글이 존재하지 않습니다.", "result": None}
        )

    return {
        "code": "200",
        "message": "지인 평가 분석에 성공했습니다.",
        "result": result
    }
