# app/ml/retrain/config.py
from pathlib import Path
import os

# ---------- 기본 경로 ----------
PROJECT_ROOT = Path(__file__).resolve().parents[3]  # project_root/
R_DATA_DIR = PROJECT_ROOT / "data"
R_TEST_DIR = R_DATA_DIR / "test"

# ---------- 모델 / 어댑터 ----------
R_MODEL_DIR = PROJECT_ROOT / "app" / "model"
R_ADAPTERS_DIR = R_MODEL_DIR / "adapters"
R_REGISTRY_PATH = R_MODEL_DIR / "registry.json"

# ---------- 평가 데이터 ----------
R_KOTE_TEST_PATH = R_TEST_DIR / "kote_test_L1L0.csv"
R_GOE_TEST_PATH = R_TEST_DIR / "goe_test_L1L0.csv"

# ✅ L1 매핑은 프로젝트 루트에 존재
R_L1_MAP_PATH = PROJECT_ROOT / "L1_id_map.json"

# ---------- 베이스 모델 경로 (.env 권장) ----------
R_BASE_MODEL_PATH = os.getenv(
    "SENTIMENT_MODEL_PATH",
    "C:/Users/james/Desktop/model/local_train/results/run_9/checkpoint-13035"
)

# ---------- LoRA 학습 기본 설정 ----------
R_LORA_R = int(os.getenv("LORA_R", "8"))
R_LORA_ALPHA = int(os.getenv("LORA_ALPHA", "16"))
R_LORA_DROPOUT = float(os.getenv("LORA_DROPOUT", "0.1"))
R_LORA_TARGET_MODULES = os.getenv("LORA_TARGET_MODULES", "query,value").split(",")

R_NUM_EPOCHS = int(os.getenv("NUM_EPOCHS", "1"))  # 확정: 1 epoch
R_BATCH_SIZE = int(os.getenv("BATCH_SIZE", "8"))
R_LEARNING_RATE = float(os.getenv("LEARNING_RATE", "5e-5"))
R_MAX_LEN = int(os.getenv("MAX_LEN", "256"))

# ---------- 교체 기준 ----------
R_MIN_MICRO_F1 = float(os.getenv("MIN_MICRO_F1", "0.6000"))
R_MIN_MACRO_F1 = float(os.getenv("MIN_MACRO_F1", "0.5000"))
R_REQUIRE_BETTER_THAN_BASE = os.getenv("REQUIRE_BETTER_THAN_BASE", "true").lower() == "true"

# 현재 운영 베이스라인 (run_9)
R_BASE_MICRO_F1 = float(os.getenv("BASE_MICRO_F1", "0.6693"))
R_BASE_MACRO_F1 = float(os.getenv("BASE_MACRO_F1", "0.5853"))
