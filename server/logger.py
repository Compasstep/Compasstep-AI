import logging
import sys
import os

from dotenv import load_dotenv

# 환경변수 전역변수로 호출
load_dotenv()
LOG_LEVEL = os.getenv("LOG_LEVEL")

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


def _build_handler() -> logging.Handler:
    handler = logging.StreamHandler(sys.stdout)
    fmt = "[%(levelname)s] [%(asctime)s] - %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    handler.setFormatter(ColorLevelFormatter(fmt=fmt, datefmt=datefmt))
    return handler


def setup_logging() -> None:
    """
    .env 파일의 LOG_LEVEL을 기반으로 로깅 레벨 설정
    기본값은 INFO
    """
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, log_level_str, logging.INFO)

    handler = _build_handler()

    # root
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)

    # uvicorn/fastapi 로거들 통일
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi", "starlette"):
        lg = logging.getLogger(name)
        lg.handlers = [handler]
        lg.propagate = False
        lg.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)