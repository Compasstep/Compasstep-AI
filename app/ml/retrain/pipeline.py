# app/ml/retrain/pipeline.py
from app.ml.retrain.dataset import load_retraining_data, load_test_dataset, mark_retraining_as_learned
from app.ml.retrain.trainer import LoraTrainer
from app.ml.retrain.evaluator_test_only import TestEvaluator
from app.ml.retrain.manager import AdapterManager
from app.core.logger import get_logger

logger = get_logger("retrain.pipeline")

def run_retraining_pipeline(limit: int = 10000):
    logger.info("🚀 [START] Retraining pipeline 시작 (limit=%d)", limit)
    df_train = load_retraining_data(limit=limit)
    if df_train.empty:
        logger.warning("⚠️ 학습할 데이터가 없습니다. Pipeline 종료")
        return {"status": "skipped", "reason": "no_data"}

    trainer = LoraTrainer()
    adapter_path = trainer.train(df_train)

    test_df = load_test_dataset()
    evaluator = TestEvaluator(adapter_path=adapter_path)
    scores = evaluator.evaluate(test_df)

    manager = AdapterManager()
    result = manager.try_register(adapter_path, scores)

    mark_retraining_as_learned()

    logger.info("✅ [DONE] Retraining 완료: %s", result)
    return result

# 👇 실행 트리거 추가
if __name__ == "__main__":
    run_retraining_pipeline()
