# tests/test_session_dual.py
import asyncio
from datetime import datetime

# app 구조 맞춰 import (필요 시 경로 조정)
from app.db.session import get_db, async_session
from app.db.models.reputation_analysis import ReputationAnalysis  # 당신 DB 테이블 중 하나 예시

# -------------------------------
# ① 동기 세션 테스트
# -------------------------------
def test_sync_insert():
    """동기 세션이 제대로 작동하는지 확인"""
    print("✅ [SYNC TEST] 시작")

    for db in get_db():  # generator yield 구조
        obj = ReputationAnalysis(
            user_id=1,
            song_title="동기테스트",
            artist_name="SYNC_ARTIST",
            sentiment_summary={"positive": 0.1, "negative": 0.2, "neutral": 0.7},
            emotion_details={"joy_happiness": 0.5, "neutral_misc": 0.5},
            keywords=["sync", "test"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(obj)
        db.commit()
        print("✅ [SYNC] Insert 완료:", obj.id)
        break  # yield라서 한 번만 실행됨


# -------------------------------
# ② 비동기 세션 테스트
# -------------------------------
async def test_async_insert():
    """비동기 세션이 제대로 작동하는지 확인"""
    print("✅ [ASYNC TEST] 시작")

    async with async_session() as session:
        obj = ReputationAnalysis(
            user_id=1,
            song_title="비동기테스트",
            artist_name="ASYNC_ARTIST",
            sentiment_summary={"positive": 0.8, "negative": 0.1, "neutral": 0.1},
            emotion_details={"admiration": 0.6, "joy_happiness": 0.4},
            keywords=["async", "test"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        session.add(obj)
        await session.commit()
        print("✅ [ASYNC] Insert 완료:", obj.id)

#
#이 파일만 바로 실행해보면 동기 세션과 비동기 세션이 잘 도는지 확인가능합니다.
#

# -------------------------------
# ③ 전체 실행 진입점
# -------------------------------
if __name__ == "__main__":
    print("🚀 DB 세션 테스트 시작\n")
    test_sync_insert()  # 동기 실행
    asyncio.run(test_async_insert())  # 비동기 실행
    print("\n🎉 모든 테스트 완료")
