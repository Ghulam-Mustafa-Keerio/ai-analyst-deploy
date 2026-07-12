from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4


@dataclass
class Experiment:
    experiment_id: str
    job_id: str
    dataset_id: str
    mode: str
    status: str = "queued"
    selected_features: list[str] = field(default_factory=list)
    selected_model: str | None = None
    metrics: dict[str, float] = field(default_factory=dict)
    insights: list[str] = field(default_factory=list)
    feature_importance: list[dict[str, Any]] = field(default_factory=list)


class ExperimentStore:
    def __init__(self) -> None:
        self._experiments: dict[str, Experiment] = {}
        self._job_index: dict[str, str] = {}

    def create(self, *, job_id: str, dataset_id: str, mode: str) -> Experiment:
        experiment = Experiment(str(uuid4()), job_id, dataset_id, mode)
        self._experiments[experiment.experiment_id] = experiment
        self._job_index[job_id] = experiment.experiment_id
        return experiment

    def by_job(self, job_id: str) -> Experiment:
        return self._experiments[self._job_index[job_id]]

    def update_job(self, job_id: str, **changes: Any) -> Experiment:
        experiment = self.by_job(job_id)
        for key, value in changes.items():
            setattr(experiment, key, value)
        return experiment

    def list(self) -> list[dict[str, Any]]:
        return [asdict(experiment) for experiment in self._experiments.values()]


experiment_store = ExperimentStore()
