# main.py
from fastapi import FastAPI
from server import logger

app = FastAPI()

@app.get("/healthcheck")
def healthcheck():
    logger.info("Health Checked.")
    return {"status": "active"}