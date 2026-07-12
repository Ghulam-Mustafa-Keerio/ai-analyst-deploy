from __future__ import annotations

from backend.agents.planner import AgentContext
from backend.tools.evaluation import summarize_metrics


class InsightGenerationAgent:
    name = "InsightGenerationAgent"

    async def run(self, context: AgentContext) -> AgentContext:
        context.insights = summarize_metrics(context.training_result.get("metrics", {}))
        if context.quality_report.get("high_missing_columns"):
            columns = ", ".join(context.quality_report["high_missing_columns"][:5])
            context.insights.append(f"High-missing columns need review: {columns}.")
        return context
