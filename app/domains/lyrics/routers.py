# app/domains/lyrics/routers.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_db
from app.domains.lyrics.schemas import LyricsAnalyzeRequest, ErrorResponse, ApiResponse
from app.domains.lyrics.service import LyricsService
from app.core.logger import get_logger

logger = get_logger("lyrics_router")

router = APIRouter(prefix="/ai/user/analyze", tags=["Reputation / Lyrics"])


# ✅ 서비스 주입 방식 통일
def get_service():
    return LyricsService()


@router.post(
    "/lyrics",
    response_model=ApiResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def analyze_lyrics(
    body: LyricsAnalyzeRequest,
    svc: LyricsService = Depends(get_service),
    db: AsyncSession = Depends(get_async_db),
):
    """
    POST /ai/user/analyze/lyrics
    요청 Body:
    {
        "lyricsId": 123
    }
    """

    try:
        if not body.lyricsId:
            return ApiResponse(
                code="400",
                message="lyricsId는 필수 입력 값입니다.",
                result=None
            )

        result = await svc.analyze_and_save(db, body.lyricsId)

        if result is None:
            return ApiResponse(
                code="404",
                message="해당 가사가 존재하지 않거나 분석 결과가 없습니다.",
                result=None
            )

        return ApiResponse(
            code="200",
            message="가사 감정분석 및 보컬 코칭에 성공했습니다.",
            result=result
        )

    except ValueError as ve:
        # DB에 id 없을 때 등
        return ApiResponse(code="404", message=str(ve), result=None)

    except Exception as e:
        logger.error("가사 분석 중 오류 발생: %s", e)
        return ApiResponse(
            code="500",
            message=f"서버 내부 오류 발생: {str(e)}",
            result=None
        )
