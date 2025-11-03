# app/ml/retrain/manager.py
from __future__ import annotations
import json, shutil
from pathlib import Path
from typing import Any, Dict, List
from app.ml.retrain.config import (
    R_REGISTRY_PATH, R_MIN_MICRO_F1, R_MIN_MACRO_F1,
    R_REQUIRE_BETTER_THAN_BASE, R_BASE_MICRO_F1, R_BASE_MACRO_F1
)

class AdapterManager:
    """✅ F1 기준으로 어댑터 관리"""
    def __init__(self, registry_path: Path | str = R_REGISTRY_PATH):
        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.registry_path.exists():
            self._save([])

    def _load(self):
        try: return json.loads(self.registry_path.read_text(encoding="utf-8"))
        except: return []
    def _save(self, data):
        self.registry_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _meets_thresholds(self, s): return (s["micro_f1"] >= R_MIN_MICRO_F1) and (s["macro_f1"] >= R_MIN_MACRO_F1)
    def _better_than_base(self, s):
        return True if not R_REQUIRE_BETTER_THAN_BASE else (s["micro_f1"] >= R_BASE_MICRO_F1 and s["macro_f1"] >= R_BASE_MACRO_F1)

    def try_register(self, adapter_path: str, scores: Dict[str, float]) -> Dict[str, Any]:
        ok_t, ok_b = self._meets_thresholds(scores), self._better_than_base(scores)
        if not (ok_t and ok_b):
            shutil.rmtree(adapter_path, ignore_errors=True)
            return {"accepted": False, "reason": f"threshold_ok={ok_t}, better_than_base={ok_b}", "kept": False}

        data = self._load()
        data.append({"path": adapter_path, "score": scores, "is_active": False})
        data.sort(key=lambda x: x["score"]["micro_f1"], reverse=True)
        removed = []
        while len(data) > 5:
            worst = data.pop(-1)
            removed.append(worst["path"])
            shutil.rmtree(worst["path"], ignore_errors=True)

        for d in data: d["is_active"] = False
        data[0]["is_active"] = True
        self._save(data)
        return {"accepted": True, "removed": removed, "active": data[0]["path"], "scores": data[0]["score"]}

    def get_active_adapter(self) -> str | None:
        for d in self._load():
            if d.get("is_active"): return d["path"]
        return None
