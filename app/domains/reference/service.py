from urllib.parse import unquote
from sqlalchemy.orm import Session

from app.agent.agent import build_agent_executor
from app.core.logger import get_logger
from app.db.repository.chat_repository import create_chat
from app.db.repository.user_repository import (
    get_user_by_id,
    update_user_status,
    count_guardrails_in_last_hour,
)
from app.domains.reference.exceptions import (
    UserSuspendedError,
    UserNotFoundError,
    AgentExecutionError,
)

logger = get_logger("app.domains.reference.service")

# 앱 시작 시 AgentExecutor 생성 (싱글톤처럼 재사용)
agent_executor = build_agent_executor()


def process_discovery(db: Session, user_id: int, query: str) -> tuple[str, bool]:
    logger.info("process_discovery 시작 - user_id=%s, raw_query=%s", user_id, query)

    if not query or not query.strip():
        logger.warning("빈 쿼리 요청 수신 - user_id=%s", user_id)
        raise ValueError("요청값이 올바르지 않습니다.")

    # 1) 유저 상태 확인
    user = get_user_by_id(db, user_id)
    if not user:
        logger.error("존재하지 않는 유저 - user_id=%s", user_id)
        raise UserNotFoundError("존재하지 않는 사용자입니다.")
    logger.debug("유저 상태 확인 - user_id=%s, status=%s", user_id, user.status)
    if user.status != "NORMAL":
        logger.warning("차단된 유저 접근 - user_id=%s, status=%s", user_id, user.status)
        raise UserSuspendedError(f"❗현재 계정 상태가 {user.status} 이므로 서비스를 이용할 수 없습니다.")

    decoded_q = unquote(query)
    logger.debug("쿼리 디코딩 완료 - user_id=%s, decoded_q=%s", user_id, decoded_q)

    try:
        # 2) Agent 실행
        logger.info("AgentExecutor 실행 시작 - user_id=%s", user_id)
        result = agent_executor.invoke({"input": decoded_q})
        logger.debug("AgentExecutor 실행 결과 - user_id=%s, result=%s", user_id, result)

        output = result.get("output")
        if isinstance(output, dict):
            safe_answer = output.get("message", "")
            # ✅ 키 이름 정확히 사용
            is_guardrailed = bool(output.get("is_guardrailed"))
            logger.info("가드레일 dict 응답 처리 - user_id=%s, is_guardrailed=%s", user_id, is_guardrailed)
        else:
            safe_answer = str(output) if output else ""
            is_guardrailed = False
            logger.info("일반 응답 처리 - user_id=%s, is_guardrailed=False", user_id)

        # 3) 채팅 기록 저장
        try:
            logger.debug("채팅 기록 저장 시도 - user_id=%s, content=%s, is_guardrailed=%s",
                         user_id, decoded_q, is_guardrailed)
            create_chat(db, user_id=user_id, content=decoded_q, is_guardrailed=is_guardrailed)
            db.commit()

            logger.info("채팅 기록 저장 성공 - user_id=%s", user_id)
        except Exception as db_err:
            db.rollback()
            logger.error("DB 저장 실패 - user_id=%s, error=%s", user_id, db_err)
            raise

        # 4) 가드레일 위반 횟수 검사
        if is_guardrailed:
            guard_count = count_guardrails_in_last_hour(db, user_id)
            logger.warning("가드레일 위반 감지 - user_id=%s, 최근 1시간 위반 횟수=%s", user_id, guard_count)

            if guard_count >= 10:
                logger.error("유저 정지 처리 - user_id=%s, 위반 횟수=%s", user_id, guard_count)
                update_user_status(db, user_id, "SUSPENDED", "가드레일 10회 이상 위반 (1시간 내)")
                db.commit()
                raise UserSuspendedError("❗가드레일 위반이 10회 누적되어 계정이 정지(SUSPENDED)되었습니다.")

        logger.info("process_discovery 완료 - user_id=%s, is_guardrailed=%s", user_id, is_guardrailed)
        return safe_answer, is_guardrailed

    except (UserSuspendedError, UserNotFoundError):
        raise
    except Exception as e:
        logger.error("Agent 실행 중 내부 오류 발생 - user_id=%s, error=%s", user_id, e)
        raise AgentExecutionError("Agent 실행 중 내부 오류가 발생했습니다.")
