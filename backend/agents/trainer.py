from __future__ import annotations

import os
from pathlib import Path

from backend.agents.planner import AgentContext
from backend.tools.data_loader import read_dataset
from backend.tools.ml_training import train_model


EXPORT_DIR = Path("/tmp/data/models") if os.environ.get("VERCEL") else Path("data/models")


class TrainingAgent:
    name = "TrainingAgent"

    async def run(self, context: AgentContext) -> AgentContext:
        if not context.target:
            raise ValueError("A target column is required for training.")
        if not context.selected_features:
            raise ValueError("At least one feature is required for training.")
        df = await read_dataset(context.dataset_path)
        context.training_result.update(
            await train_model(
                df,
                target=context.target,
                features=context.selected_features,
                model_name=context.selected_model or "random_forest",
                export_dir=str(EXPORT_DIR),
            )
        )
        return context


class EvaluationAgent:
    name = "EvaluationAgent"

    async def run(self, context: AgentContext) -> AgentContext:
        context.training_result["evaluation_status"] = "accepted"
        return context
