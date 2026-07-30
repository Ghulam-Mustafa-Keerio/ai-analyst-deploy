"""Experiment tracking integration.

Provides a unified ``ExperimentTracker`` abstraction that supports:
* **MLflow** (local or remote tracking server) — preferred for open-source.
* **Weights & Biases** — optional, enabled when ``WANDB_API_KEY`` is set.
* **In-memory fallback** — always available, mirrors ``ExperimentStore``.

The tracker is *optional*: if neither MLflow nor W&B is installed/configured,
calls degrade to no-ops and the in-memory store is used. This keeps the
platform runnable with zero extra dependencies.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator

from backend.memory.experiment_store import experiment_store


@dataclass
class RunContext:
    run_id: str
    experiment_id: str
    backend: str  # "mlflow" | "wandb" | "memory"
    metrics: dict[str, float] = field(default_factory=dict)
    params: dict[str, Any] = field(default_factory=dict)
    artifacts: list[str] = field(default_factory=list)


class ExperimentTracker:
    """Unified experiment tracking with graceful degradation."""

    def __init__(self) -> None:
        self._backend = self._detect_backend()
        self._mlflow = None
        self._wandb = None
        self._init_backend()

    # ------------------------------------------------------------------
    # Backend detection
    # ------------------------------------------------------------------
    def _detect_backend(self) -> str:
        if os.environ.get("WANDB_API_KEY"):
            try:
                import wandb  # noqa: F401
                return "wandb"
            except ImportError:
                pass
        if os.environ.get("MLFLOW_TRACKING_URI") or os.environ.get("MLFLOW_TRACKING_URL"):
            try:
                import mlflow  # noqa: F401
                return "mlflow"
            except ImportError:
                pass
        # Try importing mlflow even without explicit URI (local file store).
        try:
            import mlflow  # noqa: F401
            return "mlflow"
        except ImportError:
            pass
        return "memory"

    def _init_backend(self) -> None:
        if self._backend == "mlflow":
            try:
                import mlflow
                tracking_uri = os.environ.get(
                    "MLFLOW_TRACKING_URI",
                    os.environ.get("MLFLOW_TRACKING_URL", "file:./data/mlruns"),
                )
                mlflow.set_tracking_uri(tracking_uri)
                self._mlflow = mlflow
            except ImportError:
                self._backend = "memory"
        elif self._backend == "wandb":
            try:
                import wandb
                self._wandb = wandb
            except ImportError:
                self._backend = "memory"

    @property
    def backend(self) -> str:
        return self._backend

    # ------------------------------------------------------------------
    # Run lifecycle
    # ------------------------------------------------------------------
    @contextmanager
    def start_run(
        self,
        *,
        experiment_name: str = "ai-analyst",
        run_name: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> Iterator[RunContext]:
        if self._backend == "mlflow" and self._mlflow:
            yield from self._mlflow_run(experiment_name, run_name, tags or {})
        elif self._backend == "wandb" and self._wandb:
            yield from self._wandb_run(experiment_name, run_name, tags or {})
        else:
            yield from self._memory_run(experiment_name, run_name, tags or {})

    def _mlflow_run(
        self, experiment_name: str, run_name: str | None, tags: dict[str, str]
    ) -> Iterator[RunContext]:
        mlflow = self._mlflow
        mlflow.set_experiment(experiment_name)
        with mlflow.start_run(run_name=run_name) as run:
            for k, v in tags.items():
                mlflow.set_tag(k, v)
            ctx = RunContext(
                run_id=run.info.run_id,
                experiment_id=run.info.experiment_id,
                backend="mlflow",
            )
            try:
                yield ctx
            finally:
                self._flush_mlflow(ctx)

    def _flush_mlflow(self, ctx: RunContext) -> None:
        mlflow = self._mlflow
        for k, v in ctx.metrics.items():
            mlflow.log_metric(k, v)
        for k, v in ctx.params.items():
            mlflow.log_param(k, v)
        for path in ctx.artifacts:
            try:
                mlflow.log_artifact(path)
            except Exception:  # noqa: BLE001
                pass

    def _wandb_run(
        self, experiment_name: str, run_name: str | None, tags: dict[str, str]
    ) -> Iterator[RunContext]:
        wandb = self._wandb
        run = wandb.init(project=experiment_name, name=run_name, tags=list(tags.keys()))
        ctx = RunContext(run_id=run.id, experiment_id=experiment_name, backend="wandb")
        try:
            yield ctx
        finally:
            wandb.log({**ctx.metrics, **{f"param/{k}": v for k, v in ctx.params.items()}})
            run.finish()

    def _memory_run(
        self, experiment_name: str, run_name: str | None, tags: dict[str, str]
    ) -> Iterator[RunContext]:
        from uuid import uuid4
        ctx = RunContext(
            run_id=str(uuid4()),
            experiment_id=experiment_name,
            backend="memory",
        )
        yield ctx

    # ------------------------------------------------------------------
    # Convenience: track a completed experiment from the store
    # ------------------------------------------------------------------
    def track_experiment(self, job_id: str) -> RunContext | None:
        """Log a finished experiment (from ``ExperimentStore``) to the tracker."""
        try:
            exp = experiment_store.by_job(job_id)
        except KeyError:
            return None
        with self.start_run(run_name=f"job-{job_id[:8]}") as run:
            run.params = {
                "mode": exp.mode,
                "dataset_id": exp.dataset_id,
                "selected_model": exp.selected_model or "auto",
                "n_features": len(exp.selected_features),
            }
            run.metrics = dict(exp.metrics)
        return run


experiment_tracker = ExperimentTracker()
