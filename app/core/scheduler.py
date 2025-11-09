#app/core/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from app.ml.retrain.pipeline import run_retraining_pipeline
from app.core.logger import get_logger
import logging

logging.getLogger("apscheduler.scheduler").setLevel(logging.WARNING)
logging.getLogger("apscheduler.executors").setLevel(logging.WARNING)
logger = get_logger("app.core.scheduler")

scheduler = BackgroundScheduler(timezone="Asia/Seoul")

def start_scheduler():
    scheduler.add_job(run_retraining_pipeline, 'cron', day=1, hour=3, minute=0)
    scheduler.start()
    logger.info("✅ Retraining scheduler started (매월 1일 03:00) at %s", datetime.now())
