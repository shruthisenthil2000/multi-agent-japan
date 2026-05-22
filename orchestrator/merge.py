"""Coordinator merge: specialist packs → draft markdown itinerary."""

from __future__ import annotations

import json
from typing import Any, Optional

from agents.runner import load_prompt
from llm.client import LLMClient, get_client
from llm.rate_limiter import ProviderRateLimiter
from llm.schemas import LLM_ONLY_WARNING, TravelBrief
from orchestrator.config import get_settings


def _summarize_pack(name: str, data: dict[str, Any], max_chars: int = 2500) -> str:
    text = json.dumps(data, ensure_ascii=False)
    if len(text) > max_chars:
        text = text[: max_chars - 15] + "…truncated"
    return f"### {name}\n{text}\n"


async def merge_itinerary(
    brief: dict[str, Any],
    research: dict[str, Any],
    lodging: dict[str, Any],
    logistics: dict[str, Any],
    budget: dict[str, Any],
    *,
    validation_gaps: Optional[list[dict[str, Any]]] = None,
    limiter: Optional[ProviderRateLimiter] = None,
    client: Optional[LLMClient] = None,
) -> str:
    settings = get_settings()
    provider = settings.provider_for_agent("merge")
    if client is None:
        client = get_client(provider, settings=settings)
    if settings.rate_limit_enabled and limiter is not None:
        await limiter.acquire(provider)

    tb = TravelBrief.model_validate(brief)
    title = ", ".join(d.city for d in tb.destinations)
    gap_note = ""
    if validation_gaps:
        gap_note = "\n\nFix these validation gaps:\n" + json.dumps(validation_gaps, indent=2)

    user = (
        f"# Trip plan: {tb.duration_days} days — {title}\n\n"
        f"TravelBrief:\n{json.dumps(brief, ensure_ascii=False)}\n\n"
        + _summarize_pack("ResearchPack", research)
        + _summarize_pack("LodgingPlan", lodging)
        + _summarize_pack("LogisticsPlan", logistics)
        + _summarize_pack("BudgetPlan", budget)
        + gap_note
    )

    system = load_prompt("merge")
    markdown = client.complete(system, user)
    if LLM_ONLY_WARNING not in markdown:
        markdown += f"\n\n*{LLM_ONLY_WARNING}*\n"
    return markdown
