# app/core/logger.py
import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from typing import Iterable

from dotenv import load_dotenv

# 환경 변수 로드 및 기본 설정
load_dotenv()
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_DIR = os.getenv("LOG_DIR", "logs")           # 기본 logs
LOG_FILE = os.getenv("LOG_FILE", "app.log")      # 기본 app.log
LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", LOG_DIR, LOG_FILE)
# 위 경로 계산 결과: 프로젝트 루트 기준 logs/app.log

# 디렉터리 생성
abs_log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", LOG_DIR))
os.makedirs(abs_log_dir, exist_ok=True)

# 콘솔 컬러 포맷터
LEVEL_COLORS = {
    "DEBUG": "\033[94m",
    "INFO": "\033[92m",
    "WARNING": "\033[93m",
    "ERROR": "\033[91m",
    "CRITICAL": "\033[95m",
}
RESET = "\033[0m"


class ColorLevelFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        original_level = record.levelname
        color = LEVEL_COLORS.get(original_level, "")
        record.levelname = f"{color}{original_level}{RESET}" if color else original_level
        try:
            return super().format(record)
        finally:
            record.levelname = original_level


def _build_console_handler() -> logging.Handler:
    handler = logging.StreamHandler(sys.stdout)
    fmt = "[%(levelname)s] [%(asctime)s] [%(name)s] - %(message)s"
    datetime = "%Y-%m-%d %H:%M:%S"
    handler.setFormatter(ColorLevelFormatter(fmt=fmt, datefmt=datetime))
    return handler


def _build_file_handler() -> logging.Handler:
    """
    logs/app.log에 회전 로그로 저장.
    - 10MB 이상이면 롤오버
    - 백업은 5개까지 유지
    """
    # 프로젝트 루트 기준 절대 경로로 계산
    log_abs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", LOG_DIR, LOG_FILE))
    handler = RotatingFileHandler(
        log_abs_path, maxBytes=10_000_000, backupCount=5, encoding="utf-8"
    )
    fmt = "[%(levelname)s] [%(asctime)s] [%(name)s] - %(message)s"
    datetime = "%Y-%m-%d %H:%M:%S"
    handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datetime))
    return handler


def _attach_handlers(logger: logging.Logger, handlers: Iterable[logging.Handler], level: int) -> None:
    logger.handlers = []
    for h in handlers:
        logger.addHandler(h)
    logger.setLevel(level)
    logger.propagate = False


def setup_logging() -> None:
    """
    .env의 LOG_LEVEL을 읽어 전역 로깅을 설정한다.
    - 콘솔(컬러) + 파일(logs/app.log) 동시 기록
    - uvicorn/fastapi/starlette 로거까지 동일 핸들러 부착
    """
    # 레벨 계산
    level = getattr(logging, LOG_LEVEL, logging.INFO)

    # 핸들러 구성
    console_handler = _build_console_handler()
    file_handler = _build_file_handler()

    # root 로거
    root = logging.getLogger()
    _attach_handlers(root, (console_handler, file_handler), level)

    # 프레임워크 로거들 통일
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi", "starlette"):
        lg = logging.getLogger(name)
        _attach_handlers(lg, (console_handler, file_handler), level)

    # 외부 라이브러리 로거 레벨 조정 (DEBUG flood 방지)
    noisy_libs = [
        "httpx",
        "httpcore",
        "urllib3",
        "openai",
        "langchain",
        "langsmith",
    ]
    for lib in noisy_libs:
        logging.getLogger(lib).setLevel(logging.WARNING)  # 필요 시 INFO or ERROR

def get_logger(name: str) -> logging.Logger:
    """
    모듈별 로거 획득용 헬퍼
    """
    return logging.getLogger(name)
