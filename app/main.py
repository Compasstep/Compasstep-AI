# app/main.py
from fastapi import FastAPI
from app.core.logger import setup_logging, get_logger

setup_logging()
logger = get_logger("app.main")

app = FastAPI(title="Compasstep FastAPI")


@app.get("/healthcheck")
def healthcheck():
    logger.info("Health Checked.")
    return {"status": "active"}


@app.get("/logger-test")
def logger_test():
    logger.info("Logger Test")
    logger.debug("Logger Test")
    logger.warning("Logger Test")
    logger.error("Logger Test")
    logger.critical("Logger Test")
    return {"status": "active"}