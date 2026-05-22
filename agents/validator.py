from __future__ import annotations

from agents.base import AgentContext, AgentResult, BaseAgent
from agents.runner import _compact_json, run_json_agent
from llm.schemas import TravelBrief, ValidationReport


class ValidatorAgent(BaseAgent):
    name = "validator"

    async def arun(self, ctx: AgentContext, draft_markdown: str, **kwargs) -> AgentResult:
        brief = TravelBrief.model_validate(ctx.travel_brief)
        user = (
            f"TravelBrief:\n{_compact_json(brief.model_dump(mode='json'))}\n\n"
            f"Draft itinerary:\n{draft_markdown[:12000]}"
        )
        _, result = await run_json_agent(
            self.name,
            ctx,
            ValidationReport,
            user,
            keep_budget_typical=True,
            **kwargs,
        )
        return result
