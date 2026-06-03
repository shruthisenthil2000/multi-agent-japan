"""Intent parser unit tests (mock LLM — no API quota)."""

import json
from pathlib import Path

import pytest

from agents.base import AgentContext
from agents.intent_parser import IntentParserAgent
from llm.schemas import TravelBrief

FIXTURES = Path(__file__).parent / "fixtures"


def test_intent_parser_canonical_mock(mock_completion_fn, disable_rate_limit):
    import asyncio

    from llm.client import get_client

    request = (
        "Plan a 5-day trip to Japan. Tokyo + Kyoto. $3,000 budget. "
        "Love food and temples, hate crowds."
    )
    ctx = AgentContext(run_id="test-intent")
    agent = IntentParserAgent()
    client = get_client("groq", completion_fn=mock_completion_fn)

    async def _run():
        return await agent.arun(ctx, request, limiter=None, client=client)

    result = asyncio.run(_run())
    brief = TravelBrief.model_validate(result.payload)
    assert brief.duration_days == 5
    assert brief.destinations[0].city == "Tokyo"
    assert brief.destinations[0].days == 3
    assert brief.destinations[1].city == "Kyoto"
    assert brief.destinations[1].days == 2
    assert brief.budget.amount == 3000
    assert "food" in brief.preferences
    assert "temples" in brief.preferences
    assert "crowds" in brief.anti_preferences
    assert ctx.travel_brief is not None


def test_intent_fixture_matches_canonical_brief():
    data = json.loads((FIXTURES / "travel_brief_valid.json").read_text())
    brief = TravelBrief.model_validate(data)
    assert sum(d.days for d in brief.destinations) == brief.duration_days
