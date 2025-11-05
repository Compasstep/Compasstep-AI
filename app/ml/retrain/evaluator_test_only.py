# app/ml/retrain/evaluator_test_only.py
from __future__ import annotations
import numpy as np, pandas as pd, torch
from sklearn.metrics import f1_score
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from peft import PeftModel
from app.ml.retrain.config import R_BASE_MODEL_PATH, R_MAX_LEN
from app.ml.retrain.dataset import load_l1_map

class TestEvaluator:
    """✅ test 전용 평가 (polarity 미사용)"""
    def __init__(self, base_model_path: str = R_BASE_MODEL_PATH, adapter_path: str | None = None, device: str | None = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.L1_ID_MAP = load_l1_map()
        self.num_labels = len(self.L1_ID_MAP)

        self.tokenizer = AutoTokenizer.from_pretrained(base_model_path)
        base = AutoModelForSequenceClassification.from_pretrained(
            base_model_path, num_labels=self.num_labels, problem_type="multi_label_classification"
        )
        self.model = PeftModel.from_pretrained(base, adapter_path) if adapter_path else base
        self.model.to(self.device)
        self.model.eval()

    def _predict_probs(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        probs_all = []
        for i in tqdm(range(0, len(texts), batch_size), desc="Evaluating"):
            batch = texts[i:i+batch_size]
            enc = self.tokenizer(batch, padding=True, truncation=True, max_length=R_MAX_LEN, return_tensors="pt").to(self.device)
            with torch.no_grad():
                logits = self.model(**enc).logits
                probs = torch.sigmoid(logits).cpu().numpy()
            probs_all.append(probs)
        return np.vstack(probs_all)

    def evaluate(self, test_df: pd.DataFrame, threshold: float = 0.5) -> dict:
        texts = test_df["text"].tolist()
        probs = self._predict_probs(texts)
        preds = (probs > threshold).astype(int)

        labels = np.zeros_like(preds, dtype=int)
        for i, ids in enumerate(test_df["l1_label_ids"].tolist()):
            for k in ids:
                if 0 <= k < self.num_labels:
                    labels[i][k] = 1

        micro = f1_score(labels, preds, average="micro", zero_division=0)
        macro = f1_score(labels, preds, average="macro", zero_division=0)
        return {"micro_f1": float(micro), "macro_f1": float(macro)}

