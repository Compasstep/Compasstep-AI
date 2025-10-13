from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from starlette import status

from app.domains.reference.schemas import DiscoveryRequest, ApiResponse, AnswerResult
from app.domains.reference.service import process_discovery
from app.db.session import get_db
from app.domains.reference.exceptions import (
    UserSuspendedError,
    UserNotFoundError,
    AgentExecutionError,
)

chat_router = APIRouter(prefix="/ai/user", tags=["discovery"])


@chat_router.post("/discovery/keyword", response_model=ApiResponse)
async def discovery_keyword(req: DiscoveryRequest, db: Session = Depends(get_db)):
    try:
        safe_answer, is_guardrailed = process_discovery(db, req.user_id, req.query)

        if is_guardrailed:
            # 가드레일 케이스: 422 + 본문에 안내 메시지
            payload = ApiResponse(
                code="422",  # 혹은 POLICY_VIOLATION 등
                message=safe_answer,  # moderation_tool이 준 안전 안내문
            )
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=payload.model_dump()
            )

        return ApiResponse(
            code="200",
            message="레퍼런스 탐색 요청을 성공적으로 전달했습니다.",
            result=AnswerResult(answer=safe_answer),
        )

    except UserSuspendedError as ue:
        return ApiResponse(
            code="403",  # Forbidden
            message=str(ue),
            result=None,
        )
    except UserNotFoundError as unfe:
        return ApiResponse(
            code="404",  # Not Found
            message=str(unfe),
            result=None,
        )
    except ValueError as ve:
        return ApiResponse(
            code="400",  # Bad Request
            message=str(ve),
            result=None,
        )
    except AgentExecutionError as ae:
        return ApiResponse(
            code="500",  # Internal Server Error
            message=str(ae),
            result=None,
        )
    except Exception as e:
        # 최종 fallback
        return ApiResponse(
            code="500",
            message=f"예상치 못한 오류 발생: {str(e)}",
            result=None,
        )
