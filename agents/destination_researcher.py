from __future__ import annotations

from agents.base import AgentContext, AgentResult, BaseAgent
from agents.runner import _compact_json, run_json_agent
from llm.schemas import ResearchPack, TravelBrief


class DestinationResearcherAgent(BaseAgent):
    name = "destination_researcher"

    async def arun(self, ctx: AgentContext, **kwargs) -> AgentResult:
        brief = TravelBrief.model_validate(ctx.travel_brief)
        user = f"TravelBrief:\n{_compact_json(brief.model_dump(mode='json'))}"
        _, result = await run_json_agent(self.name, ctx, ResearchPack, user, **kwargs)
        return result
