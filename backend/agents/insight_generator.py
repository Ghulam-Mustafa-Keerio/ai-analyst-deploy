from __future__ import annotations

import json

from backend.agents.planner import AgentContext
from backend.llm import get_llm
from backend.tools.evaluation import summarize_metrics


_SYSTEM = (
    "You are a data-science communicator. Given an experiment summary, write 2-3 "
    "plain-language insights a business stakeholder would act on. Mention the top "
    "driver (feature importance) and any data-quality caveats. Respond ONLY as JSON: "
    '{"insights":["<sentence>", ...]}.'
)


class InsightGenerationAgent:
    name = "InsightGenerationAgent"

    async def run(self, context: AgentContext) -> AgentContext:
        base = summarize_metrics(context.training_result.get("metrics", {}))
        llm = get_llm()
        if llm is not None:
            llm_insights = await self._llm_insights(llm, context)
            if llm_insights:
                context.insights = llm_insights
                self._append_caveats(context)
                return context
        # Deterministic fallback.
        context.insights = base
        self._append_caveats(context)
        return context

    @staticmethod
    def _append_caveats(context: AgentContext) -> None:
        if context.quality_report.get("high_missing_columns"):
            columns = ", ".join(context.quality_report["high_missing_columns"][:5])
            context.insights.append(f"High-missing columns need review: {columns}.")
        if context.quality_report.get("leakage_columns"):
            columns = ", ".join(context.quality_report["leakage_columns"][:5])
            context.insights.append(f"Possible target leakage in: {columns}. Verify before trusting metrics.")

    @staticmethod
    async def _llm_insights(llm, context: AgentContext) -> list[str] | None:
        from backend.llm.provider import extract_json

        summary = {
            "domain": context.profile.get("domain", {}).get("domain"),
            "task": context.training_result.get("task"),
            "model": context.selected_model,
            "metrics": context.training_result.get("metrics", {}),
            "top_features": [fi["feature"] for fi in context.training_result.get("feature_importance", [])[:3]],
            "high_missing": context.quality_report.get("high_missing_columns", []),
            "leakage": context.quality_report.get("leakage_columns", []),
        }
        prompt = f"Experiment summary: {json.dumps(summary)}"
        text = await llm.complete(prompt, system=_SYSTEM, temperature=0.4, max_tokens=900)
        if not text:
            return None
        try:
            parsed = extract_json(text)
            # The model may return either {"insights": [...]} or a bare [...].
            if isinstance(parsed, list):
                insights = parsed
            else:
                insights = (parsed or {}).get("insights") or []
            return [str(i) for i in insights if i]
        except (KeyError, TypeError):
            return None
