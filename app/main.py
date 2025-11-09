# app/main.py
from fastapi import FastAPI
from app.core.logger import setup_logging, get_logger
from app.domains.reference.routers import chat_router
from app.domains.reputation.routers import router as reputation_router
from app.domains.peer_reputation.routers import router as peer_router
from app.core.scheduler import start_scheduler


setup_logging()
logger = get_logger("app.main")

app = FastAPI(title="Compasstep FastAPI")

routers = [
    chat_router,
    reputation_router,
    peer_router
]

for r in routers:
    app.include_router(r)



@app.get("/healthcheck")
def healthcheck():
    logger.info("Health Checked.")
    return {"status": "active"}

@app.on_event("startup")
def on_startup():
    start_scheduler()

# ✅ RabbitMQ consumer 실행
#@app.on_event("startup")
#async def startup_event():
#    loop = asyncio.get_event_loop()
#    loop.create_task(start_consumer())