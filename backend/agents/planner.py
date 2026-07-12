from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentContext:
    job_id: str
    dataset_id: str
    dataset_path: str
    mode: str = "autonomous"
    target: str | None = None
    requested_features: list[str] = field(default_factory=list)
    requested_model: str | None = None
    profile: dict[str, Any] = field(default_factory=dict)
    quality_report: dict[str, Any] = field(default_factory=dict)
    selected_features: list[str] = field(default_factory=list)
    selected_model: str | None = None
    training_result: dict[str, Any] = field(default_factory=dict)
    insights: list[str] = field(default_factory=list)


class PlannerAgent:
    name = "PlannerAgent"

    async def run(self, context: AgentContext) -> AgentContext:
        if context.mode not in {"manual", "assisted", "autonomous"}:
            context.mode = "autonomous"
        return context
