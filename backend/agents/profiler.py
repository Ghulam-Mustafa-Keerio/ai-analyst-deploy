from __future__ import annotations

from backend.agents.planner import AgentContext
from backend.tools.domain_detection import detect_domain
from backend.tools.data_loader import profile_dataset


class DataProfilerAgent:
    name = "DataProfilerAgent"

    async def run(self, context: AgentContext) -> AgentContext:
        context.profile = await profile_dataset(context.dataset_path)
        context.profile["domain"] = detect_domain(list(context.profile["schema"]))
        if not context.target:
            columns = list(context.profile["schema"])
            context.target = columns[-1] if columns else None
        return context


class DataQualityAgent:
    name = "DataQualityAgent"

    async def run(self, context: AgentContext) -> AgentContext:
        missing = context.profile.get("missing_ratio", {})
        high_missing = [column for column, ratio in missing.items() if ratio > 0.3]
        context.quality_report = {
            "high_missing_columns": high_missing,
            "row_count": context.profile.get("rows", 0),
            "column_count": context.profile.get("columns", 0),
            "status": "review" if high_missing else "ready",
        }
        return context
