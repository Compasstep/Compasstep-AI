# app/core/cache.py
import redis
import json
import os
from app.core.logger import get_logger

logger = get_logger("cache")

# ---------------------------------------------------------------------------
# 🧠 Redis 캐시 유틸
# ---------------------------------------------------------------------------
class RedisCache:
    def __init__(self):
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", "6379"))
        self.ttl = int(os.getenv("REDIS_TTL_SECONDS", 7 * 24 * 3600))
        self.client = redis.Redis(
            host=self.host,
            port=self.port,
            decode_responses=True
        )

    def set_json(self, key: str, value: dict):
        """JSON 객체를 Redis에 저장"""
        try:
            self.client.set(key, json.dumps(value))
            self.client.expire(key, self.ttl)
            logger.info(f"✅ Redis 저장 완료: key={key}, TTL={self.ttl}s")
        except Exception as e:
            logger.error(f"⚠️ Redis 저장 실패 (key={key}): {e}")

    def get_json(self, key: str) -> dict | None:
        """Redis에서 JSON 객체 조회"""
        try:
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"⚠️ Redis 조회 실패 (key={key}): {e}")
            return None
