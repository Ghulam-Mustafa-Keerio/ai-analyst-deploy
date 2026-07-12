from __future__ import annotations

from backend.agents.planner import AgentContext
from backend.tools.ml_training import choose_model


class ModelSelectionAgent:
    name = "ModelSelectionAgent"

    async def run(self, context: AgentContext) -> AgentContext:
        context.selected_model = choose_model(context.profile, context.mode, context.requested_model)
        return context


class ModelDebateAgent:
    name = "ModelDebateAgent"

    async def run(self, context: AgentContext) -> AgentContext:
        # Lightweight deterministic debate trace; model selection remains auditable.
        context.training_result["model_debate"] = [
            {"model": "linear", "position": "fast baseline and interpretable coefficients"},
            {"model": "random_forest", "position": "robust default for nonlinear and mixed-type data"},
        ]
        return context
