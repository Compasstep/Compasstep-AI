from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from starlette import status

from typing import List
from app.domains.reference.schemas import DiscoveryRequest, ApiResponse, TrackVideo
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
            payload = ApiResponse(
                code="422",
                message=str(safe_answer) if not isinstance(safe_answer, str) else safe_answer,
            )
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=payload.model_dump()
            )

        # 리스트 정규화
        items: List[dict] = []
        if isinstance(safe_answer, list):
            items = [x for x in safe_answer if isinstance(x, (dict, str))]
        elif isinstance(safe_answer, dict):
            items = [safe_answer]
        elif isinstance(safe_answer, str):
            items = [{
                "videoId": "",
                "title": safe_answer,
                "channelName": "",
                "thumbnailUrl": "",
                "youtubeUrl": "",
            }]

        if not items:
            return ApiResponse(code="204", message="추천 결과가 없습니다.", result=None)

        # Pydantic 검증
        videos = []
        for obj in items:
            if isinstance(obj, str):
                obj = {
                    "videoId": "",
                    "title": obj,
                    "channelName": "",
                    "thumbnailUrl": "",
                    "youtubeUrl": "",
                }
            videos.append(TrackVideo(**obj))

        return ApiResponse(
            code="200",
            message="레퍼런스 탐색 요청을 성공적으로 전달했습니다.",
            result=videos,  # 여러 개 그대로 반환
        )

    except UserSuspendedError as ue:
        return ApiResponse(code="403", message=str(ue), result=None)
    except UserNotFoundError as unified:
        return ApiResponse(code="404", message=str(unified), result=None)
    except ValueError as ve:
        return ApiResponse(code="400", message=str(ve), result=None)
    except AgentExecutionError as ae:
        return ApiResponse(code="500", message=str(ae), result=None)
    except Exception as e:
        return ApiResponse(code="500", message=f"예상치 못한 오류 발생: {str(e)}", result=None)
