from __future__ import annotations

from backend.agents.planner import AgentContext


class FeatureSelectionAgent:
    name = "FeatureSelectionAgent"

    async def run(self, context: AgentContext) -> AgentContext:
        columns = list(context.profile.get("schema", {}))
        usable = [column for column in columns if column != context.target]
        if context.mode == "manual" and context.requested_features:
            context.selected_features = [column for column in context.requested_features if column in usable]
        else:
            missing = context.profile.get("missing_ratio", {})
            context.selected_features = [column for column in usable if missing.get(column, 0) < 0.5]
        return context
