# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from app.core.constants import psycopg_connection_uri, ASYNC_DB_URI  # DB 연결 URI (env에서 불러온 값)

# =====================================================
# 동기 엔진
# =====================================================
# SQLAlchemy 엔진 생성 (PostgreSQL 최적화 옵션 포함)
engine = create_engine(
    psycopg_connection_uri,
    pool_size=10,               # 기본 연결 풀 크기
    max_overflow=10,            # 최대 초과 연결
    pool_timeout=15,            # 커넥션 풀에서 가져올 때 최대 대기 시간 (초)
    pool_recycle=900,           # 900초(15분)마다 연결 재생성 → DB idle timeout 방지
    pool_pre_ping=True,         # 연결 유효성 체크 (죽은 연결 방지)
    pool_reset_on_return="commit",  # 커밋 후 연결 초기화
    pool_use_lifo=True,         # LIFO 정책 → 최근 연결 먼저 사용
    connect_args={
        "application_name": "compasstep-ai",   # PostgreSQL 세션에서 app 이름 보임
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 3,
        "options": "-c statement_timeout=60000",  # 60초 타임아웃
        "prepare_threshold": 0,
    },
)

# 세션 팩토리
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,  # 커밋 후 객체 접근 가능하도록
)

# 의존성 주입용 헬퍼 (FastAPI Depends)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =====================================================
# 비동기 엔진 (FastAPI async 전용)
# =====================================================
async_uri = ASYNC_DB_URI  # <- 직관적이고 안전

# 디버그: 실제 사용되는 URI 출력 (테스트 시 확인)
print(f"🔍 [DEBUG] sync URI (psycopg_connection_uri) = {psycopg_connection_uri}")
print(f"🔍 [DEBUG] async_engine URI (async_uri) = {async_uri}")

async_engine = create_async_engine(
    async_uri,
    pool_size=10,
    max_overflow=10,
    pool_timeout=15,
    pool_recycle=900,
    pool_pre_ping=True,
    connect_args={
        "server_settings": {
            "application_name": "compasstep-ai",
        }
    },
)

async_session = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

async def get_async_db():
    async with async_session() as session:
        yield session