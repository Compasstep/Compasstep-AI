# app/ml/retrain/trainer.py
from __future__ import annotations
from typing import List
from pathlib import Path
import time, numpy as np, torch
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from peft import LoraConfig, get_peft_model
from app.ml.retrain.config import (
    R_BASE_MODEL_PATH, R_ADAPTERS_DIR,
    R_LORA_R, R_LORA_ALPHA, R_LORA_DROPOUT, R_LORA_TARGET_MODULES,
    R_NUM_EPOCHS, R_BATCH_SIZE, R_LEARNING_RATE, R_MAX_LEN
)
from app.ml.retrain.dataset import load_l1_map

class LoraTrainer:
    """✅ 1 epoch 고정 학습"""
    def __init__(self, base_model_path: str = R_BASE_MODEL_PATH, output_root: Path | str = R_ADAPTERS_DIR):
        self.base_model_path = base_model_path
        self.output_root = Path(output_root)
        self.output_root.mkdir(parents=True, exist_ok=True)
        self.L1_ID_MAP = load_l1_map()
        self.num_labels = len(self.L1_ID_MAP)

    def _build_dataset(self, df) -> Dataset:
        texts = df["text"].tolist()
        labels = []
        for ids in df["l1_label_ids"].tolist():
            vec = np.zeros(self.num_labels, dtype=np.float32)
            for i in ids:
                if 0 <= i < self.num_labels:
                    vec[i] = 1.0
            labels.append(vec)
        return Dataset.from_dict({"text": texts, "labels": labels})

    def train(self, df) -> str:
        tokenizer = AutoTokenizer.from_pretrained(self.base_model_path)
        base_model = AutoModelForSequenceClassification.from_pretrained(
            self.base_model_path, num_labels=self.num_labels, problem_type="multi_label_classification"
        )
        lora_cfg = LoraConfig(
            r=R_LORA_R, lora_alpha=R_LORA_ALPHA, target_modules=R_LORA_TARGET_MODULES,
            lora_dropout=R_LORA_DROPOUT, bias="none", task_type="SEQ_CLS"
        )
        model = get_peft_model(base_model, lora_cfg)
        ds = self._build_dataset(df)

        def preprocess(batch):
            enc = tokenizer(batch["text"], padding="max_length", truncation=True, max_length=R_MAX_LEN)
            enc["labels"] = batch["labels"]
            return enc

        ds = ds.map(preprocess, batched=True, remove_columns=["text"])
        out_dir = self.output_root / f"adapter_{int(time.time())}"

        args = TrainingArguments(
            output_dir=str(out_dir),
            per_device_train_batch_size=R_BATCH_SIZE,
            per_device_eval_batch_size=R_BATCH_SIZE,
            learning_rate=R_LEARNING_RATE,
            num_train_epochs=R_NUM_EPOCHS,
            logging_steps=20,
            save_strategy="no",
            report_to=[]
        )

        trainer = Trainer(model=model, args=args, train_dataset=ds)
        trainer.train()
        model.save_pretrained(str(out_dir))
        return str(out_dir)
