# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.constants import psycopg_connection_uri  # DB 연결 URI (env에서 불러온 값)

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
