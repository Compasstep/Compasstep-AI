# app/domains/reputation/consumer.py
import asyncio
import json
from aio_pika import connect_robust, IncomingMessage
from app.domains.reputation.service import YoutubeReputationServiceAsync
from app.db.session import async_session
from app.core.logger import get_logger

logger = get_logger("app.domains.reputation.consumer")

async def handle_message(msg: IncomingMessage):
    """RabbitMQ에서 들어온 메시지를 처리"""
    async with msg.process():
        try:
            payload = json.loads(msg.body.decode())
            user_id = payload.get("userId", 1)
            song_title = payload.get("songTitle")
            artist = payload.get("artist")

            if not song_title or not artist:
                logger.warning("❌ Invalid message payload: missing songTitle or artist")
                return

            # ✅ 기존 service 재사용
            svc = YoutubeReputationServiceAsync()
            async with async_session() as db:
                await svc.analyze_youtube_reputation(song_title, artist, db, user_id)

            logger.info(f"✅ [{song_title}] 분석 완료 (user_id={user_id})")

        except Exception as e:
            logger.error(f"❌ 메시지 처리 중 오류 발생: {e}")


async def start_consumer():
    """RabbitMQ 연결 및 큐 소비 시작"""
    connection = await connect_robust("amqp://guest:guest@localhost/")
    channel = await connection.channel()
    queue = await channel.declare_queue("reputation.analyze", durable=True)

    logger.info("🚀 RabbitMQ consumer started (queue=reputation.analyze)")
    await queue.consume(handle_message)

    return connection
