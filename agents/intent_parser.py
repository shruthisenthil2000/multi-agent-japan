from __future__ import annotations

from agents.base import AgentContext, AgentResult, BaseAgent
from agents.runner import run_json_agent
from llm.schemas import TravelBrief


class IntentParserAgent(BaseAgent):
    name = "intent_parser"

    async def arun(self, ctx: AgentContext, user_request: str, **kwargs) -> AgentResult:
        _, result = await run_json_agent(
            self.name,
            ctx,
            TravelBrief,
            f"User request:\n{user_request}",
            **kwargs,
        )
        ctx.travel_brief = result.payload
        return result


def parse_intent(ctx: AgentContext, user_request: str, **kwargs) -> TravelBrief:
    import asyncio

    agent = IntentParserAgent()
    result = asyncio.run(agent.arun(ctx, user_request, **kwargs))
    return TravelBrief.model_validate(result.payload)
