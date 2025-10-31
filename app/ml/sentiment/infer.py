# app/ml/sentiment/infer.py
from __future__ import annotations
from typing import List, Dict, Tuple
import json, os
from pathlib import Path
import torch

# ---- [선택] 실제 모델 사용: transformers/torch가 없으면 친절히 안내 ----
_USE_DUMMY = False
try:
    import torch  # type: ignore
    from transformers import AutoTokenizer, AutoModelForSequenceClassification  # type: ignore
except Exception:
    _USE_DUMMY = True

# ====== L1 라벨 20개 로드 ======
_THIS_DIR = Path(__file__).resolve().parent
_L1_PATH = _THIS_DIR.parent.parent.parent / "L1_id_map.json"  # repo 루트에 있는 파일 기준
with open(_L1_PATH, "r", encoding="utf-8") as f:
    L1_ID_MAP: Dict[str, int] = json.load(f)
ID2LABEL = {v: k for k, v in L1_ID_MAP.items()}

# ====== 감정→극성 매핑 (사용자 제공 스펙을 코드화) ======
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

def _majority_polarity_from_emotions(prob: Dict[str, float], top_k: int = 6) -> str:
    """댓글 하나에 대해 ‘상위 k 감정’의 개수 다수결로 polarity 결정."""
    tops = sorted(prob.items(), key=lambda x: x[1], reverse=True)[:top_k]
    bucket = {"positive": 0, "negative": 0, "neutral": 0}
    for lbl, _p in tops:
        pol = POLARITY_OF.get(lbl, "neutral")
        bucket[pol] += 1
    # 다수결, 동률이면 확률 합이 큰 쪽
    max_cnt = max(bucket.values())
    cands = [k for k, v in bucket.items() if v == max_cnt]
    if len(cands) == 1:
        return cands[0]
    # 동률 깨기: 해당 polarity에 속하는 확률 합
    sums = {pol: sum(prob[l] for l in prob if POLARITY_OF.get(l, "neutral") == pol) for pol in cands}
    return max(sums.items(), key=lambda x: x[1])[0]

class SentimentModel:
    """더미↔실모델 호환 인터페이스 (predict_batch 반환 구조 동일)."""

    def __init__(self, model_name_or_path: str | None = None, device: str | None = None):
        self.use_dummy = _USE_DUMMY or (model_name_or_path is None)
        if self.use_dummy:
            print("[SentimentModel] Using DUMMY predictions.")
            self.model = None
            self.tokenizer = None
            return

        self.tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_name_or_path, num_labels=len(L1_ID_MAP)
        )
        self.model.eval()
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        self.model.to(self.device)
        print(f"[SentimentModel] Loaded {model_name_or_path} on {self.device}")

    @torch.inference_mode()
    def _predict_one_batch(self, batch_texts: List[str]) -> List[Dict[str, float]]:
        toks = self.tokenizer(
            batch_texts,
            padding=True,
            truncation=True,
            max_length=256,
            return_tensors="pt",
        ).to(self.device)
        logits = self.model(**toks).logits  # (B, 20)
        probs = torch.softmax(logits, dim=-1).cpu().tolist()
        outs: List[Dict[str, float]] = []
        for row in probs:
            d = {ID2LABEL[i]: float(row[i]) for i in range(len(row))}
            outs.append(d)
        return outs

    def predict_batch(self, comments: List[str]) -> List[Dict]:
        """반환: [{'emotions': {label:prob...}, 'polarity': {pos/neg/neu}} ...]"""
        if self.use_dummy:
            import random
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
