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

# 프로젝트 루트 기준 logs/app.log 경로
log_abs_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", LOG_DIR, LOG_FILE)
)
os.makedirs(os.path.dirname(log_abs_path), exist_ok=True)

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
    handler.setFormatter(ColorLevelFormatter(fmt=fmt, datefmt="%Y-%m-%d %H:%M:%S"))
    return handler


def _build_file_handler() -> logging.Handler:
    handler = RotatingFileHandler(
        log_abs_path, maxBytes=10_000_000, backupCount=5, encoding="utf-8"
    )
    fmt = "[%(levelname)s] [%(asctime)s] [%(name)s] - %(message)s"
    handler.setFormatter(logging.Formatter(fmt=fmt, datefmt="%Y-%m-%d %H:%M:%S"))
    return handler


def _attach_handlers(logger: logging.Logger, handlers: Iterable[logging.Handler], level: int) -> None:
    logger.handlers = []
    for h in handlers:
        logger.addHandler(h)
    logger.setLevel(level)
    logger.propagate = False


def setup_logging() -> None:
    """
    전역 로깅 설정
    - 콘솔(컬러) + 파일(logs/app.log) 동시 기록
    - uvicorn/fastapi/starlette 로거 레벨은 조정
    - noisy 라이브러리는 WARNING 이상으로 제한
    """
    level = getattr(logging, LOG_LEVEL, logging.INFO)

    console_handler = _build_console_handler()
    file_handler = _build_file_handler()

    # root logger
    root = logging.getLogger()
    _attach_handlers(root, (console_handler, file_handler), level)

    # Uvicorn 관련 로거: access 로그는 너무 verbose하니 WARNING 이상
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(level)
    logging.getLogger("uvicorn").setLevel(level)

    # FastAPI & Starlette 로거
    logging.getLogger("fastapi").setLevel(level)
    logging.getLogger("starlette").setLevel(level)

    # noisy 라이브러리 로거: DEBUG flood 방지
    noisy_libs = ["httpx", "httpcore", "urllib3", "openai", "langchain", "langsmith", "pylast"]
    for lib in noisy_libs:
        logging.getLogger(lib).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
