from __future__ import annotations

from backend.agents.planner import AgentContext
from backend.tools.domain_detection import detect_domain
from backend.tools.data_loader import profile_dataset
from backend.tools.ml_training import infer_task_from_profile


class DataProfilerAgent:
    name = "DataProfilerAgent"

    async def run(self, context: AgentContext) -> AgentContext:
        context.profile = await profile_dataset(context.dataset_path)
        context.profile["domain"] = detect_domain(list(context.profile["schema"]))
        if not context.target:
            columns = list(context.profile["schema"])
            context.target = columns[-1] if columns else None
        # Surface the inferred task early so upstream agents (debate, selection)
        # can reason about candidate models before training runs.
        context.training_result["task"] = infer_task_from_profile(context.profile, context.target)
        return context


class DataQualityAgent:
    name = "DataQualityAgent"

    async def run(self, context: AgentContext) -> AgentContext:
        missing = context.profile.get("missing_ratio", {})
        high_missing = [column for column, ratio in missing.items() if ratio > 0.3]
        # Leakage heuristic: a feature that is a near-perfect proxy for the
        # target (e.g. an ID, label copy, or post-outcome field) inflates
        # offline metrics and breaks in production. Flag suspicious columns.
        leakage = self._detect_leakage(context)
        status = "review" if (high_missing or leakage) else "ready"
        context.quality_report = {
            "high_missing_columns": high_missing,
            "leakage_columns": leakage,
            "row_count": context.profile.get("rows", 0),
            "column_count": context.profile.get("columns", 0),
            "status": status,
        }
        return context

    @staticmethod
    def _detect_leakage(context: AgentContext) -> list[str]:
        target = context.target
        if not target:
            return []
        schema = context.profile.get("schema", {})
        target_type = schema.get(target, "")
        suspicious = []
        # Common leakage naming patterns (suffixes that imply outcome/label).
        leak_suffixes = ("_id", "id", "label", "target", "outcome", "result", "score", "flag", "is_", "has_")
        for column in schema:
            if column == target:
                continue
            low = column.lower()
            if any(low.endswith(suffix) or low.startswith(suffix) for suffix in leak_suffixes):
                suspicious.append(column)
        return suspicious
