"""Shared LLM agent execution with prompts, rate limits, and provenance."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional, TypeVar

from pydantic import BaseModel

from agents.base import AgentContext, AgentResult
from llm.client import LLMClient, get_client
from llm.rate_limiter import ProviderRateLimiter
from llm.schemas import LLM_ONLY_WARNING, DataConfidence, with_llm_provenance
from orchestrator.config import Provider, get_settings

T = TypeVar("T", bound=BaseModel)

PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(agent_name: str) -> str:
    path = PROMPTS_DIR / f"{agent_name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Missing prompt: {path}")
    return path.read_text()


def _compact_json(data: Any, max_chars: int = 6000) -> str:
    text = json.dumps(data, ensure_ascii=False)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 20] + '… (truncated)"}'


async def run_json_agent(
    agent_name: str,
    ctx: AgentContext,
    model_type: type[T],
    user_message: str,
    *,
    limiter: Optional[ProviderRateLimiter] = None,
    client: Optional[LLMClient] = None,
    keep_budget_typical: bool = False,
) -> tuple[T, AgentResult]:
    settings = get_settings()
    provider: Provider = settings.provider_for_agent(agent_name)
    if client is None:
        client = get_client(provider, settings=settings)
    if settings.rate_limit_enabled and limiter is not None:
        await limiter.acquire(provider)

    system = load_prompt(agent_name)
    model = client.complete_json(system, user_message, model_type)
    if not keep_budget_typical:
        model = with_llm_provenance(model)  # type: ignore[assignment]
    else:
        if hasattr(model, "warnings"):
            w = list(model.warnings)  # type: ignore[attr-defined]
            if LLM_ONLY_WARNING not in w:
                w.append(LLM_ONLY_WARNING)
                object.__setattr__(model, "warnings", w)
        if hasattr(model, "data_confidence"):
            object.__setattr__(model, "data_confidence", DataConfidence.typical)

    payload = model.model_dump(mode="json", by_alias=True)
    result = AgentResult(
        payload=payload,
        summary=f"{agent_name} completed",
        warnings=list(payload.get("warnings", [])),
        provider=provider,
        model=client.model,
    )
    return model, result


def run_json_agent_sync(
    agent_name: str,
    ctx: AgentContext,
    model_type: type[T],
    user_message: str,
    **kwargs: Any,
) -> tuple[T, AgentResult]:
    import asyncio

    return asyncio.run(run_json_agent(agent_name, ctx, model_type, user_message, **kwargs))
