import os
from dotenv import load_dotenv
load_dotenv()

# See docker command above to launch a postgres instance with pgvector enabled.
DB_HOST = os.getenv("POSTGRES_ENDPOINT") # Postgres(PGVector) 데이터베이스의 엔드포인트
DB_USER = os.getenv("POSTGRES_USER") # Postgres 사용자 이름
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD") # Postgres 비밀번호
DB_PORT = os.getenv("POSTGRES_PORT") # Postgres 포트
DB_NAME = os.getenv("POSTGRES_DB") # Postgres 데이터베이스 이름

psycopg_connection_uri = (
    f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    "?connect_timeout=5"
)

# psycopg_pool.ConnectionPool 용 (DSN 문자열 스타일)
psycopg_connection_string = (
    f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD} "
    "connect_timeout=5 keepalives=1 keepalives_idle=30 keepalives_interval=10 keepalives_count=3 "
    "options='-c statement_timeout=60000'"
)

# 비동기 전용 URI (명시적으로): asyncpg 드라이버 사용
# -> Windows Proactor 루프 문제를 피하려면 asyncpg 사용 권장
ASYNC_DB_URI = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# S3 용 상수
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_REGION = os.getenv("AWS_S3_REGION")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_S3_ENDPOINT = os.getenv("AWS_S3_ENDPOINT")