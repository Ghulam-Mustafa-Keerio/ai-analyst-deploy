from __future__ import annotations

from typing import Any


def summarize_metrics(metrics: dict[str, float]) -> list[str]:
    if "accuracy" in metrics:
        return [
            f"Classifier reached {metrics['accuracy']:.3f} accuracy.",
            f"Weighted F1 is {metrics.get('f1', 0.0):.3f}, useful for class-imbalance review.",
        ]
    return [
        f"Regressor reached {metrics.get('r2', 0.0):.3f} R2.",
        f"Mean absolute error is {metrics.get('mae', 0.0):.3f}.",
    ]


def compare_experiments(experiments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(experiments, key=lambda item: max(item.get("metrics", {"score": 0}).values(), default=0), reverse=True)
