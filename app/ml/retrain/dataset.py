# app/ml/retrain/dataset.py
from __future__ import annotations
from typing import List, Optional
import os, json
from pathlib import Path
import pandas as pd

try:
    import psycopg2  # type: ignore
except Exception:
    psycopg2 = None

from app.ml.retrain.config import (
    R_KOTE_TEST_PATH, R_GOE_TEST_PATH, R_L1_MAP_PATH
)

# ---------- L1 매핑 로드 ----------
def load_l1_map() -> dict:
    with open(R_L1_MAP_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ---------- test 세트 로드 ----------
def load_test_dataset(kote_path: Path | str = R_KOTE_TEST_PATH,
                      goe_path: Path | str = R_GOE_TEST_PATH) -> pd.DataFrame:
    df_kote = pd.read_csv(kote_path)
    df_goe  = pd.read_csv(goe_path)
    df = pd.concat([df_kote, df_goe], ignore_index=True)

    def _parse_ids(x):
        if isinstance(x, list):
            return x
        if isinstance(x, str):
            return json.loads(x)
        return []
    df["l1_label_ids"] = df["l1_label_ids"].apply(_parse_ids)
    return df[["text", "l1_label_ids"]].copy()

# ---------- retraining_data 로드 ----------
def load_retraining_data(limit: int = 10000,
                         db_url: Optional[str] = None) -> pd.DataFrame:
    if psycopg2 is None:
        raise RuntimeError("psycopg2 설치 필요")
    db_url = db_url or os.getenv("DATABASE_URL", "postgresql://root:1234@localhost:5432/compasstep")
    conn = psycopg2.connect(db_url)
    query = """
        SELECT comment_text AS text, prediction
        FROM retraining_data
        WHERE is_reviewed = true AND is_learned = false
        LIMIT %s
    """
    df = pd.read_sql(query, conn, params=(limit,))
    conn.close()

    def _parse(x):
        if isinstance(x, str):
            try: return json.loads(x)
            except: return []
        return x if isinstance(x, list) else []

    df["prediction"] = df["prediction"].apply(_parse)
    L1_ID_MAP = load_l1_map()
    def _to_ids(names: List[str]) -> List[int]:
        return [L1_ID_MAP[n] for n in names if n in L1_ID_MAP]
    df["l1_label_ids"] = df["prediction"].apply(_to_ids)
    df = df.drop(columns=["prediction"])
    return df[["text", "l1_label_ids"]].copy()

# ---------- 학습 완료 표시 ----------
def mark_retraining_as_learned(db_url: Optional[str] = None) -> None:
    if psycopg2 is None:
        raise RuntimeError("psycopg2 설치 필요")
    db_url = db_url or os.getenv("DATABASE_URL", "postgresql://root:1234@localhost:5432/compasstep")
    conn = psycopg2.connect(db_url)
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE retraining_data
            SET is_learned = true
            WHERE is_reviewed = true AND is_learned = false
        """)
        conn.commit()
    conn.close()
