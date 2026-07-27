from __future__ import annotations

import asyncio
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd


# Model zoo: the candidate set the debate/selection agents reason over. Each
# entry documents the task it serves and *why* it is a sensible candidate, which
# the deterministic debate fallback surfaces when no LLM is configured.
MODEL_ZOO: dict[str, dict[str, str]] = {
    "linear": {"task": "both", "why": "Fast, interpretable baseline with linear coefficients."},
    "random_forest": {"task": "both", "why": "Robust default for nonlinear and mixed-type data."},
    "gradient_boosting": {"task": "both", "why": "Often wins on tabular accuracy via sequential error correction."},
    "svm": {"task": "both", "why": "Strong on high-dimensional, well-scaled feature spaces."},
    "knn": {"task": "both", "why": "Simple, instance-based baseline useful for small clean datasets."},
}


def infer_task(y: pd.Series) -> str:
    if y.dtype.kind in "ifu" and y.nunique(dropna=True) > 20:
        return "regression"
    return "classification"


def infer_task_from_profile(profile: dict[str, Any], target: str | None) -> str:
    """Best-effort task detection from a profile before the data is fully loaded.

    Used by upstream agents (debate, selection) that run before training.
    """
    if not target:
        return "classification"
    schema = profile.get("schema", {})
    dtype = schema.get(target, "")
    # Numeric types whose dtype string starts with int/float/uint.
    is_numeric = any(dtype.lower().startswith(t) for t in ("int", "float", "uint"))
    if not is_numeric:
        return "classification"
    # For numeric targets, check the count of distinct values from the numeric
    # summary.  ``DataFrame.describe()`` stores ``count`` (non-null rows), not
    # unique values.  A safer heuristic: if std is very small relative to count
    # (i.e. values cluster tightly), or the column name hints at a label, treat
    # as classification.  Without unique count in the summary, we fall back to
    # a dtype-based guess: integers with count <= 20 are likely categorical.
    numeric_summary = profile.get("numeric_summary", {}).get(target)
    if numeric_summary:
        try:
            count = numeric_summary.get("count", 0)
            std = numeric_summary.get("std", 1)
            # Low std relative to range suggests few distinct values.
            mean_val = numeric_summary.get("mean", 0)
            min_val = numeric_summary.get("min", 0)
            max_val = numeric_summary.get("max", 0)
            value_range = max_val - min_val
            # If the range is small (e.g. 0-1, 0-10) it's likely categorical.
            if isinstance(value_range, (int, float)) and value_range <= 20:
                return "classification"
            if isinstance(count, (int, float)) and count > 20:
                return "regression"
        except (TypeError, AttributeError):
            pass
    return "classification"


def build_model(model_name: str, task: str) -> Any:
    from sklearn.ensemble import (
        GradientBoostingClassifier,
        GradientBoostingRegressor,
        RandomForestClassifier,
        RandomForestRegressor,
    )
    from sklearn.linear_model import LogisticRegression, Ridge
    from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
    from sklearn.svm import SVC, SVR

    reg = {
        "linear": Ridge(),
        "random_forest": RandomForestRegressor(n_estimators=120, random_state=42),
        "gradient_boosting": GradientBoostingRegressor(random_state=42),
        "svm": SVR(),
        "knn": KNeighborsRegressor(),
    }
    clf = {
        "linear": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "random_forest": RandomForestClassifier(n_estimators=120, random_state=42, class_weight="balanced"),
        "gradient_boosting": GradientBoostingClassifier(random_state=42),
        "svm": SVC(probability=True, random_state=42, class_weight="balanced"),
        "knn": KNeighborsClassifier(),
    }
    return reg[model_name] if task == "regression" else clf[model_name]


def choose_model(profile: dict[str, Any], mode: str, requested_model: str | None = None) -> str:
    if mode == "manual" and requested_model:
        return requested_model
    if profile["columns"] > 30 or any(value > 0.15 for value in profile["missing_ratio"].values()):
        return "random_forest"
    return "linear"


def _safe_split_size(row_count: int, n_classes: int = 1) -> float | int:
    """Return a held-out test size that ``train_test_split`` will accept.

    For small datasets an absolute count is safer than a fraction, but it must
    still leave at least one sample per class in the test set (classification)
    and at least one training sample. The caller guarantees the dataset is large
    enough to split before calling this; here we only pick a valid magnitude.
    """
    if row_count < 10:
        return max(n_classes, 1)
    return 0.2


async def train_model(
    df: pd.DataFrame,
    *,
    target: str,
    features: list[str],
    model_name: str,
    export_dir: str | None = None,
) -> dict[str, Any]:
    def _train() -> dict[str, Any]:
        from sklearn.compose import ColumnTransformer
        from sklearn.impute import SimpleImputer
        from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, r2_score
        from sklearn.model_selection import (
            GridSearchCV,
            KFold,
            StratifiedKFold,
            cross_val_score,
            train_test_split,
        )
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import OneHotEncoder, StandardScaler

        X = df[features]
        y = df[target]
        usable = y.notna()
        X = X.loc[usable]
        y = y.loc[usable]
        if len(y) < 3:
            raise ValueError("Training requires at least three rows with a non-null target.")
        task = infer_task(y)
        if task == "classification" and y.nunique(dropna=True) < 2:
            raise ValueError("Classification requires at least two target classes.")
        numeric_features = X.select_dtypes(include="number").columns.tolist()
        categorical_features = [column for column in X.columns if column not in numeric_features]
        preprocessor = ColumnTransformer(
            transformers=[
                ("num", Pipeline([("imputer", SimpleImputer()), ("scaler", StandardScaler())]), numeric_features),
                ("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]), categorical_features),
            ]
        )
        base_model = build_model(model_name, task)
        pipeline = Pipeline([("preprocessor", preprocessor), ("model", base_model)])

        # --- Split first so HPO and evaluation both use the held-out set ----
        stratify = y if task == "classification" and y.value_counts().min() > 1 else None
        n_classes = int(y.nunique(dropna=True)) if task == "classification" else 1
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=_safe_split_size(len(y), n_classes),
            random_state=42,
            stratify=stratify,
        )

        # --- Hyperparameter optimization (light, deterministic) -----------
        param_grid = _param_grid(model_name, task)
        if param_grid:
            cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42) if task == "classification" else KFold(n_splits=3, shuffle=True, random_state=42)
            try:
                search = GridSearchCV(pipeline, param_grid, cv=cv, scoring="f1_weighted" if task == "classification" else "r2", n_jobs=1)
                search.fit(X_train, y_train)
                pipeline = search.best_estimator_
                best_params = search.best_params_
            except Exception:
                pipeline.fit(X_train, y_train)
                best_params = {}
        else:
            pipeline.fit(X_train, y_train)
            best_params = {}

        # --- Held-out evaluation (no re-fitting) --------------------------
        predictions = pipeline.predict(X_test)
        if task == "regression":
            metrics = {"r2": float(r2_score(y_test, predictions)), "mae": float(mean_absolute_error(y_test, predictions))}
        else:
            metrics = {"accuracy": float(accuracy_score(y_test, predictions)), "f1": float(f1_score(y_test, predictions, average="weighted"))}

        # --- Cross-validation stability (variance across folds) ----------
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42) if task == "classification" else KFold(n_splits=5, shuffle=True, random_state=42)
        scoring = "accuracy" if task == "classification" else "r2"
        try:
            cv_scores = cross_val_score(pipeline, X, y, cv=cv, scoring=scoring, n_jobs=1)
            metrics["cv_mean"] = float(cv_scores.mean())
            metrics["cv_std"] = float(cv_scores.std())
        except Exception:
            metrics["cv_mean"] = metrics.get("r2", metrics.get("accuracy", 0.0))
            metrics["cv_std"] = 0.0

        # --- Feature importance (aggregated to original feature names) ----
        model = pipeline.named_steps["model"]
        importances = getattr(model, "feature_importances_", None)
        if importances is None:
            importances = getattr(model, "coef_", None)
            if importances is not None:
                importances = importances.ravel()
        feature_importance = []
        if importances is not None:
            # After one-hot encoding, the model has more features than the
            # original input.  Map encoded feature names back to original
            # columns and sum their importances.
            try:
                encoded_names = pipeline.named_steps["preprocessor"].get_feature_names_out()
                aggregated: dict[str, float] = {f: 0.0 for f in features}
                for enc_name, imp in zip(encoded_names, importances, strict=False):
                    # Encoded names look like "num__age" or "cat__sex_male".
                    # The original column is the part after the prefix, before
                    # any one-hot suffix.
                    bare = enc_name.split("__", 1)[-1] if "__" in enc_name else enc_name
                    matched = False
                    for orig in features:
                        if bare == orig or bare.startswith(orig + "_"):
                            aggregated[orig] += abs(float(imp))
                            matched = True
                            break
                    if not matched:
                        # Fallback: unmatched encoded feature — skip.
                        pass
                for feat, imp_val in aggregated.items():
                    if math.isfinite(imp_val):
                        feature_importance.append({"feature": feat, "importance": imp_val})
            except Exception:
                # Fallback: use the simple zip approach (pre-encoding only).
                for feature, importance in zip(features, importances[: len(features)], strict=False):
                    if math.isfinite(float(importance)):
                        feature_importance.append({"feature": feature, "importance": float(importance)})
        feature_importance.sort(key=lambda item: item["importance"], reverse=True)

        result: dict[str, Any] = {
            "task": task,
            "metrics": metrics,
            "feature_importance": feature_importance,
            "best_params": best_params,
            "model_name": model_name,
        }

        # --- Model persistence (deployable artifact) ---------------------
        if export_dir:
            result["model_path"] = _persist(pipeline, export_dir, model_name, features, target, task)
        return result

    return await asyncio.to_thread(_train)


def _param_grid(model_name: str, task: str) -> dict[str, list[Any]]:
    """Small, cheap grids so HPO stays fast on the serverless 4 MB tier."""
    if model_name == "random_forest":
        return {"model__n_estimators": [80, 160], "model__max_depth": [None, 8]}
    if model_name == "gradient_boosting":
        return {"model__n_estimators": [80, 160], "model__learning_rate": [0.05, 0.1]}
    if model_name == "svm":
        return {"model__C": [0.1, 1.0]}
    if model_name == "knn":
        return {"model__n_neighbors": [5, 10]}
    return {}


def _persist(pipeline: Any, export_dir: str, model_name: str, features: list[str], target: str, task: str) -> str:
    import joblib

    Path(export_dir).mkdir(parents=True, exist_ok=True)
    path = Path(export_dir) / f"model_{model_name}.joblib"
    artifact = {
        "pipeline": pipeline,
        "features": features,
        "target": target,
        "task": task,
        "model_name": model_name,
    }
    joblib.dump(artifact, path)
    return str(path)
