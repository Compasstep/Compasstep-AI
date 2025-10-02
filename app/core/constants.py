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
