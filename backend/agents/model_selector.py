from __future__ import annotations

from typing import cast

from backend.agents.planner import AgentContext
from backend.llm import LLMProvider, get_llm
from backend.tools.ml_training import choose_model, MODEL_ZOO


class ModelSelectionAgent:
    name = "ModelSelectionAgent"

    async def run(self, context: AgentContext) -> AgentContext:
        context.selected_model = choose_model(context.profile, context.mode, context.requested_model)
        return context


_SYSTEM = (
    "You are a senior ML engineer in a model-selection council. Given a dataset "
    "profile, argue the trade-offs of candidate models for THIS dataset. Be concise "
    "(one sentence per model). Respond ONLY as JSON: "
    '{"debate":[{"model":"<name>","position":"<one sentence>"}, ...]}.'
)


class ModelDebateAgent:
    name = "ModelDebateAgent"

    async def run(self, context: AgentContext) -> AgentContext:
        candidates = self._candidates(context)
        llm = get_llm()
        if llm is not None:
            debate = await self._llm_debate(llm, context, candidates)
            if debate:
                context.training_result["model_debate"] = debate
                return context
        # Deterministic fallback keeps the pipeline auditable without an LLM.
        context.training_result["model_debate"] = [
            {"model": name, "position": desc} for name, desc in candidates.items()
        ]
        return context

    @staticmethod
    def _candidates(context: AgentContext) -> dict[str, str]:
        task = context.training_result.get("task", "classification")
        # "both" models apply to either task; include them alongside task-specific ones.
        return {name: meta["why"] for name, meta in MODEL_ZOO.items() if meta["task"] in {task, "both"}}

    @staticmethod
    async def _llm_debate(llm: LLMProvider, context: AgentContext, candidates: dict[str, str]) -> list[dict[str, str]] | None:
        import json

        from backend.llm.provider import extract_json

        profile: dict[str, object] = {
            "rows": context.profile.get("rows"),
            "columns": context.profile.get("columns"),
            "domain": context.profile.get("domain", {}).get("domain"),
            "high_missing": context.quality_report.get("high_missing_columns", []),
        }
        prompt = (
            f"Dataset profile: {json.dumps(profile)}\n"
            f"Candidate models for this task: {', '.join(candidates)}.\n"
            "Provide a one-sentence position for each candidate."
        )
        text = await llm.complete(prompt, system=_SYSTEM, temperature=0.2, max_tokens=900)
        if not text:
            return None
        try:
            parsed = extract_json(text)
            # The model may return either {"debate": [...]} or a bare [...].
            # ``extract_json`` yields ``Any``, so we cast the narrowed result to a
            # concrete type to keep the rest of the pipeline free of ``Unknown``.
            entries: list[dict[str, str]] = []
            if isinstance(parsed, list):
                entries = cast("list[dict[str, str]]", parsed)
            elif isinstance(parsed, dict):
                parsed_dict = cast("dict[str, object]", parsed)
                debate_field = parsed_dict.get("debate")
                if isinstance(debate_field, list):
                    entries = cast("list[dict[str, str]]", debate_field)
            return [
                {"model": entry["model"], "position": entry["position"]}
                for entry in entries
                if "model" in entry
            ]
        except (KeyError, TypeError):
            return None
