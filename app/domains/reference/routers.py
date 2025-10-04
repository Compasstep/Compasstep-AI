from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

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
        safe_answer, is_guardrail = process_discovery(db, req.user_id, req.query)

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
