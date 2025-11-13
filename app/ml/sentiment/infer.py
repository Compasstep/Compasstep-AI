# app/ml/sentiment/infer.py
from __future__ import annotations
from typing import List, Dict, Tuple
import json, os, random
from pathlib import Path
from peft import PeftModel
from app.ml.retrain.manager import AdapterManager
from app.core.logger import get_logger

logger = get_logger("app.ml.sentiment.infer")

# =====================================================
# Dummy-safe decorator (핵심)
# =====================================================
def safe_inference_mode():
    """torch가 없으면 그냥 원본 함수를 그대로 반환"""
    if torch is None:
        def decorator(func):
            return func
        return decorator
    return torch.inference_mode()

# =====================================================
# ① Torch/Transformers Import & Dummy Safe Mode
# =====================================================
_USE_DUMMY = False
try:
    import torch  # type: ignore
    from transformers import AutoTokenizer, AutoModelForSequenceClassification  # type: ignore
    #raise ImportError("Forced import failure for testing Dummy mode") #더미 실행원하면 활성화

except Exception:
    _USE_DUMMY = True
    torch = None
    logger.warning("[SentimentModel] transformers/torch not available. Running in DUMMY mode.")

# =====================================================
# ② L1 라벨 로드
# =====================================================
_THIS_DIR = Path(__file__).resolve().parent
_L1_PATH = _THIS_DIR.parent.parent.parent / "L1_id_map.json"
with open(_L1_PATH, "r", encoding="utf-8") as f:
    L1_ID_MAP: Dict[str, int] = json.load(f)
ID2LABEL = {v: k for k, v in L1_ID_MAP.items()}

# =====================================================
# ③ 감정 → 극성 매핑
# =====================================================
MAPPING_SPEC = {
    "joy_happiness": {"polarity": "positive", "members": ["뿌듯함","즐거움/신남","흐뭇함(귀여움/예쁨)","행복","기쁨","amusement","excitement","joy","optimism","pride"]},
    "gratitude": {"polarity": "positive", "members": ["고마움","gratitude"]},
    "admiration": {"polarity": "positive", "members": ["감동/감탄","존경","admiration"]},
    "interest_curiosity": {"polarity": "positive", "members": ["기대감","신기함/관심","desire"]},
    "approval": {"polarity": "positive", "members": ["환영/호의","approval"]},
    "anger_annoyance": {"polarity": "negative", "members": ["불평/불만","화남/분노","지긋지긋","짜증","귀찮음","의심/불신","어이없음","anger","annoyance"]},
    "disgust": {"polarity": "negative", "members": ["한심함","역겨움/징그러움","증오/혐오","disgust"]},
    "sadness_grief": {"polarity": "negative", "members": ["슬픔","안타까움/실망","절망","패배/자기혐오","힘듦/지침","죄책감","서러움","불쌍함/연민","재미없음","disappointment","grief","remorse","sadness"]},
    "fear_nervousness": {"polarity": "negative", "members": ["공포/무서움","부담/안_내킴","불안/걱정","경악","fear","nervousness"]},
    "surprise": {"polarity": "neutral", "members": ["놀람","surprise"]},
    "realization": {"polarity": "neutral", "members": ["깨달음","realization"]},
    "relief": {"polarity": "positive", "members": ["편안/쾌적","안심/신뢰","relief"]},
    "caring_love": {"polarity": "positive", "members": ["아껴주는","caring","love"]},
    "embarrassment": {"polarity": "neutral", "members": ["부끄러움","당황/난처","embarrassment"]},
    "confusion": {"polarity": "neutral", "members": ["confusion"]},
    "curiosity": {"polarity": "neutral", "members": ["curiosity"]},
    "disapproval": {"polarity": "negative", "members": ["disapproval"]},
    "resolute": {"polarity": "neutral", "members": ["비장함"]},
    "arrogance": {"polarity": "neutral", "members": ["우쭐댐/무시함"]},
    "neutral_misc": {"polarity": "neutral", "members": ["없음","neutral"]},
}
POLARITY_OF = {k: v["polarity"] for k, v in MAPPING_SPEC.items()}


# =====================================================
# ④ 감정 확률 → 극성 결정
# =====================================================
def _majority_polarity_from_emotions(prob: Dict[str, float], top_k: int = 6) -> str:
    """댓글 하나에 대해 상위 k 감정의 다수결로 polarity 결정"""
    tops = sorted(prob.items(), key=lambda x: x[1], reverse=True)[:top_k]
    bucket = {"positive": 0, "negative": 0, "neutral": 0}
    for lbl, _p in tops:
        pol = POLARITY_OF.get(lbl, "neutral")
        bucket[pol] += 1

    max_cnt = max(bucket.values())
    cands = [k for k, v in bucket.items() if v == max_cnt]
    if len(cands) == 1:
        return cands[0]

    sums = {pol: sum(prob[l] for l in prob if POLARITY_OF.get(l, "neutral") == pol) for pol in cands}
    return max(sums.items(), key=lambda x: x[1])[0]


# =====================================================
# ⑤ SentimentModel 클래스 (GPU 자동 감지 + .env 지원)
# =====================================================
class SentimentModel:
    """실제 모델 or 더미모델. GPU 자동 감지 + .env 모델 경로 지원."""

    def __init__(self, model_name_or_path: str | None = None, device: str | None = None):
        self.use_dummy = _USE_DUMMY

        # --------------------------
        # 1) 모델 경로 설정 (.env 인식)
        # --------------------------
        if model_name_or_path is None:
            model_name_or_path = os.getenv(
                "SENTIMENT_MODEL_PATH",
                "C:/Users/james/Desktop/model/local_train/results/run_9/checkpoint-13035",
            )

        # --------------------------
        # 2) 디바이스 자동 감지
        # --------------------------
        if device is None:
            if not _USE_DUMMY and torch is not None:
                if torch.cuda.is_available():
                    device = "cuda"
                elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
                    device = "mps"
                else:
                    device = "cpu"
            else:
                device = "cpu"
        self.device = device

        if self.use_dummy:
            logger.warning("[SentimentModel] Using DUMMY predictions (no torch).")
            self.model = None
            self.tokenizer = None
            return

        logger.info("[SentimentModel] Loading model from %s", model_name_or_path)
        logger.info("[SentimentModel] Using device: %s", self.device)

        # --------------------------
        # 3) 모델 로드
        # --------------------------
        self.tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
        base_model = AutoModelForSequenceClassification.from_pretrained(
            model_name_or_path, num_labels=len(L1_ID_MAP)
        )

        # --------------------------
        # 4) LoRA 어댑터 병합 시도
        # --------------------------
        active_adapter = self._get_active_adapter_path()  # 새로 추가된 함수
        if active_adapter:
            logger.info("[SentimentModel] Merging active LoRA adapter: %s", active_adapter)
            try:
                base_model = PeftModel.from_pretrained(base_model, active_adapter)
                logger.info("[SentimentModel] LoRA adapter loaded successfully.")
            except Exception as e:
                logger.error("[SentimentModel] Failed to load adapter. Using base model only.", exc_info=True)
        else:
            logger.info("[SentimentModel] No active adapter found, using base model only.")

        self.model = base_model.to(self.device)
        self.model.eval()

    # =====================================================
    # 🔹 활성화된 어댑터 경로 조회 함수
    # =====================================================
    def _get_active_adapter_path(self) -> str | None:
        """현재 registry.json에서 is_active=True인 어댑터 경로 반환"""
        try:
            manager = AdapterManager()
            active = manager.get_active_adapter()
            if active:
                logger.info("[SentimentModel] Active adapter found: %s", active)
            else:
                logger.warning("[SentimentModel] No active adapter registered — using base model only.")
            return active
        except Exception as e:
            logger.error("[SentimentModel] Adapter lookup failed", exc_info=True)
            return None

    # =====================================================
    # 🔹 내부 배치 예측 함수
    # =====================================================
    @safe_inference_mode()
    def _predict_one_batch(self, batch_texts: List[str]) -> List[Dict[str, float]]:
        toks = self.tokenizer(
            batch_texts,
            padding=True,
            truncation=True,
            max_length=256,
            return_tensors="pt",
        ).to(self.device)
        logits = self.model(**toks).logits
        probs = torch.softmax(logits, dim=-1).cpu().tolist()

        outs: List[Dict[str, float]] = []
        for row in probs:
            outs.append({ID2LABEL[i]: float(row[i]) for i in range(len(row))})
        return outs

    # =====================================================
    # 🔹 외부 호출용 predict_batch
    # =====================================================
    def predict_batch(self, comments: List[str]) -> List[Dict]:
        """반환: [{'emotions': {...}, 'polarity': {...}} ...]"""
        if self.use_dummy:
            emotions = list(L1_ID_MAP.keys())
            outs = []
            for _t in comments:
                emo_probs = {e: random.random() for e in emotions}
                s = sum(emo_probs.values())
                emo_probs = {k: v / s for k, v in emo_probs.items()}
                pol = _majority_polarity_from_emotions(emo_probs, top_k=6)
                p = {"positive": 0.0, "negative": 0.0, "neutral": 0.0}
                p[pol] = 1.0
                outs.append({"emotions": emo_probs, "polarity": p})
            return outs

        B = 32
        results: List[Dict] = []
        for i in range(0, len(comments), B):
            probs_batch = self._predict_one_batch(comments[i:i+B])
            for emo_probs in probs_batch:
                pol = _majority_polarity_from_emotions(emo_probs, top_k=6)
                p = {"positive": 0.0, "negative": 0.0, "neutral": 0.0}
                p[pol] = 1.0
                results.append({"emotions": emo_probs, "polarity": p})
        return results
