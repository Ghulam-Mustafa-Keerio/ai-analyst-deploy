from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Awaitable
from uuid import uuid4

from backend.agents.feature_engineer import FeatureSelectionAgent
from backend.agents.insight_generator import InsightGenerationAgent
from backend.agents.model_selector import ModelDebateAgent, ModelSelectionAgent
from backend.agents.planner import AgentContext, PlannerAgent
from backend.agents.profiler import DataProfilerAgent, DataQualityAgent
from backend.agents.trainer import EvaluationAgent, TrainingAgent
from backend.memory.experiment_store import experiment_store
from backend.ws.event_stream import event_stream, make_event


Emitter = Callable[[dict], Awaitable[None]]


class AgentRuntime:
    def __init__(self) -> None:
        self._tasks: dict[str, asyncio.Task] = {}
        self.pipeline = [
            PlannerAgent(),
            DataProfilerAgent(),
            DataQualityAgent(),
            FeatureSelectionAgent(),
            ModelDebateAgent(),
            ModelSelectionAgent(),
            TrainingAgent(),
            EvaluationAgent(),
            InsightGenerationAgent(),
        ]

    async def start(
        self,
        *,
        dataset_id: str,
        dataset_path: str,
        mode: str = "autonomous",
        target: str | None = None,
        features: list[str] | None = None,
        model: str | None = None,
    ) -> str:
        job_id = str(uuid4())
        experiment_store.create(job_id=job_id, dataset_id=dataset_id, mode=mode)
        context = AgentContext(
            job_id=job_id,
            dataset_id=dataset_id,
            dataset_path=dataset_path,
            mode=mode,
            target=target,
            requested_features=features or [],
            requested_model=model,
        )
        self._tasks[job_id] = asyncio.create_task(self._run_pipeline(context))
        return job_id

    async def run_sync(
        self,
        *,
        dataset_id: str,
        dataset_path: str,
        mode: str = "autonomous",
        target: str | None = None,
        features: list[str] | None = None,
        model: str | None = None,
    ) -> dict:
        """Run the full pipeline inline and return the final job status.

        Used by serverless deployments (e.g. Vercel) where background tasks are
        killed when the request returns and in-memory state is not shared across
        invocations. The result is returned in a single request.
        """
        job_id = str(uuid4())
        experiment_store.create(job_id=job_id, dataset_id=dataset_id, mode=mode)
        context = AgentContext(
            job_id=job_id,
            dataset_id=dataset_id,
            dataset_path=dataset_path,
            mode=mode,
            target=target,
            requested_features=features or [],
            requested_model=model,
        )
        await self._run_pipeline(context)
        return self.status(job_id)

    async def _emit(self, context: AgentContext, *, agent: str | None, message: str, status: str, payload: dict | None = None) -> None:
        await event_stream.publish(
            make_event("agent_step", job_id=context.job_id, agent=agent, message=message, status=status, payload=payload)
        )

    async def _run_pipeline(self, context: AgentContext) -> None:
        experiment_store.update_job(context.job_id, status="running")
        await event_stream.publish(make_event("job_status", job_id=context.job_id, message="Agent pipeline started.", status="running"))
        try:
            for agent in self.pipeline:
                await self._emit(context, agent=agent.name, message=f"{agent.name} started.", status="running")
                context = await agent.run(context)
                await self._emit(context, agent=agent.name, message=self._decision_message(agent.name, context), status="completed", payload=self._payload(agent.name, context))
            experiment_store.update_job(
                context.job_id,
                status="completed",
                selected_features=context.selected_features,
                selected_model=context.selected_model,
                metrics=context.training_result.get("metrics", {}),
                insights=context.insights,
                feature_importance=context.training_result.get("feature_importance", []),
            )
            await event_stream.publish(make_event("job_status", job_id=context.job_id, message="Agent pipeline completed.", status="completed"))
        except Exception as exc:
            experiment_store.update_job(context.job_id, status="failed")
            await event_stream.publish(
                make_event("job_status", job_id=context.job_id, message=str(exc), status="failed", payload={"error": type(exc).__name__})
            )

    def status(self, job_id: str) -> dict:
        experiment = experiment_store.by_job(job_id)
        task = self._tasks.get(job_id)
        return {
            "job_id": job_id,
            "status": experiment.status,
            "done": bool(task.done()) if task else True,
            "events": event_stream.history(job_id),
        }

    @staticmethod
    def _decision_message(agent_name: str, context: AgentContext) -> str:
        messages = {
            "PlannerAgent": f"Execution mode set to {context.mode}.",
            "DataProfilerAgent": f"Profiled {context.profile.get('rows', 0)} rows and {context.profile.get('columns', 0)} columns.",
            "DataQualityAgent": f"Quality status is {context.quality_report.get('status', 'unknown')}.",
            "FeatureSelectionAgent": f"Selected {len(context.selected_features)} features.",
            "ModelDebateAgent": "Compared candidate modeling strategies.",
            "ModelSelectionAgent": f"Selected {context.selected_model} based on profile and autonomy mode.",
            "TrainingAgent": "Training completed and metrics captured.",
            "EvaluationAgent": "Evaluation accepted for experiment tracking.",
            "InsightGenerationAgent": f"Generated {len(context.insights)} insights.",
        }
        return messages.get(agent_name, f"{agent_name} completed.")

    @staticmethod
    def _payload(agent_name: str, context: AgentContext) -> dict:
        payloads = {
            "DataProfilerAgent": {"profile": context.profile},
            "DataQualityAgent": {"quality_report": context.quality_report},
            "FeatureSelectionAgent": {"selected_features": context.selected_features},
            "ModelDebateAgent": {"debate": context.training_result.get("model_debate", [])},
            "ModelSelectionAgent": {"selected_model": context.selected_model},
            "TrainingAgent": {"metrics": context.training_result.get("metrics", {})},
            "InsightGenerationAgent": {"insights": context.insights, "feature_importance": context.training_result.get("feature_importance", [])},
        }
        return payloads.get(agent_name, {})


agent_runtime = AgentRuntime()
