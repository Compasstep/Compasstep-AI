from .logger import setup_logging, get_logger

setup_logging()
# 패키지 import 시 기본 로거 바로 제공
logger = get_logger("CompassStep-AI")