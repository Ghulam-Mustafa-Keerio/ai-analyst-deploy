from __future__ import annotations

import asyncio
import math
from typing import Any

import pandas as pd


def infer_task(y: pd.Series) -> str:
    if y.dtype.kind in "ifu" and y.nunique(dropna=True) > 20:
        return "regression"
    return "classification"


def build_model(model_name: str, task: str) -> Any:
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.linear_model import LogisticRegression, Ridge

    if model_name == "linear":
        return Ridge() if task == "regression" else LogisticRegression(max_iter=1000)
    return RandomForestRegressor(n_estimators=120, random_state=42) if task == "regression" else RandomForestClassifier(n_estimators=120, random_state=42)


def choose_model(profile: dict[str, Any], mode: str, requested_model: str | None = None) -> str:
    if mode == "manual" and requested_model:
        return requested_model
    if profile["columns"] > 30 or any(value > 0.15 for value in profile["missing_ratio"].values()):
        return "random_forest"
    return "linear"


def _safe_split_size(row_count: int) -> float | int:
    if row_count < 10:
        return 1
    return 0.2


async def train_model(df: pd.DataFrame, *, target: str, features: list[str], model_name: str) -> dict[str, Any]:
    def _train() -> dict[str, Any]:
        from sklearn.compose import ColumnTransformer
        from sklearn.impute import SimpleImputer
        from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, r2_score
        from sklearn.model_selection import train_test_split
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
        pipeline = Pipeline([("preprocessor", preprocessor), ("model", build_model(model_name, task))])
        stratify = y if task == "classification" and y.value_counts().min() > 1 else None
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=_safe_split_size(len(y)),
            random_state=42,
            stratify=stratify,
        )
        pipeline.fit(X_train, y_train)
        predictions = pipeline.predict(X_test)
        if task == "regression":
            metrics = {"r2": float(r2_score(y_test, predictions)), "mae": float(mean_absolute_error(y_test, predictions))}
        else:
            metrics = {"accuracy": float(accuracy_score(y_test, predictions)), "f1": float(f1_score(y_test, predictions, average="weighted"))}
        model = pipeline.named_steps["model"]
        importances = getattr(model, "feature_importances_", None)
        feature_importance = []
        if importances is not None:
            for feature, importance in zip(features, importances[: len(features)], strict=False):
                if math.isfinite(float(importance)):
                    feature_importance.append({"feature": feature, "importance": float(importance)})
        return {"task": task, "metrics": metrics, "feature_importance": feature_importance}

    return await asyncio.to_thread(_train)
