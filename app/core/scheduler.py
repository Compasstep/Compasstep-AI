#app/core/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from app.ml.retrain.pipeline import run_retraining_pipeline

scheduler = BackgroundScheduler(timezone="Asia/Seoul")

def start_scheduler():
    scheduler.add_job(run_retraining_pipeline, 'cron', day=1, hour=3, minute=0)
    scheduler.start()
    print(f"[{datetime.now()}] ✅ Retraining scheduler started (매월 1일 03:00)")
