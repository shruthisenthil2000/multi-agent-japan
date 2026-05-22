"""Phase 1 LLM-only multi-agent travel planning pipeline."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

from agents.budget import BudgetAgent
from agents.destination_researcher import DestinationResearcherAgent
from agents.intent_parser import IntentParserAgent
from agents.lodging import LodgingAgent
from agents.logistics import LogisticsAgent
from agents.validator import ValidatorAgent
from llm.client import CompletionFn, LLMClient, clear_client_cache
from llm.rate_limiter import ProviderRateLimiter
from orchestrator.config import get_settings
from orchestrator.merge import merge_itinerary
from orchestrator.run_state import RunState

CompletionFnOptional = Optional[CompletionFn]


@dataclass
class PlanTripResult:
    run_id: str
    run_dir: str
    final_markdown: str
    validation_status: str
    artifacts: dict[str, str]


async def _timed_step(state: RunState, step: str, coro):
    t0 = time.perf_counter()
    try:
        result = await coro
        state.trace(step, duration_ms=(time.perf_counter() - t0) * 1000, status="ok")
        return result
    except Exception as e:
        state.trace(
            step,
            duration_ms=(time.perf_counter() - t0) * 1000,
            status="error",
            error=str(e),
        )
        raise


def _clients_from_mock(
    completion_fn: CompletionFn,
) -> tuple[LLMClient, LLMClient]:
    settings = get_settings()
    clear_client_cache()
    return (
        LLMClient("groq", settings=settings, completion_fn=completion_fn),
        LLMClient("gemini", settings=settings, completion_fn=completion_fn),
    )


async def plan_trip(
    request: str,
    *,
    run_id: Optional[str] = None,
    completion_fn: CompletionFnOptional = None,
    runs_base_dir: Optional["Path"] = None,
) -> PlanTripResult:
    if not request or not request.strip():
        raise ValueError("Trip request is required")

    settings = get_settings()
    state = RunState(run_id=run_id, base_dir=runs_base_dir)
    state.write_text("request", request.strip())

    limiter = ProviderRateLimiter.from_settings() if settings.rate_limit_enabled else None
    groq_client: Optional[LLMClient] = None
    gemini_client: Optional[LLMClient] = None
    if completion_fn:
        groq_client, gemini_client = _clients_from_mock(completion_fn)

    def _kwargs(agent_name: str) -> dict[str, Any]:
        kw: dict[str, Any] = {"limiter": limiter}
        prov = settings.provider_for_agent(agent_name)
        if completion_fn:
            kw["client"] = groq_client if prov == "groq" else gemini_client
        return kw

    from agents.base import AgentContext

    ctx = AgentContext(run_id=state.run_id)

    # 1. Intent (Groq)
    intent_agent = IntentParserAgent()
    intent_result = await _timed_step(
        state,
        "intent_parser",
        intent_agent.arun(ctx, request.strip(), **_kwargs("intent_parser")),
    )
    state.write_json("travel_brief", intent_result.payload)

    # 2. Parallel Groq specialists
    async def _run_specialist(agent, key: str, artifact_key: str):
        result = await agent.arun(ctx, **_kwargs(agent.name))
        ctx.artifacts[artifact_key] = result.payload
        state.write_json(key, result.payload)
        state.trace(agent.name, provider=result.provider, model=result.model, status="ok")
        return result

    dest_a = DestinationResearcherAgent()
    lod_a = LodgingAgent()
    log_a = LogisticsAgent()

    await _timed_step(
        state,
        "specialists_parallel",
        asyncio.gather(
            _run_specialist(dest_a, "research", "research"),
            _run_specialist(lod_a, "lodging", "lodging"),
            _run_specialist(log_a, "logistics", "logistics"),
        ),
    )

    # 3. Budget (Gemini) — sequential after logistics
    budget_agent = BudgetAgent()
    budget_result = await _timed_step(
        state,
        "budget",
        budget_agent.arun(ctx, **_kwargs("budget")),
    )
    state.write_json("budget", budget_result.payload)
    ctx.artifacts["budget"] = budget_result.payload

    # 4. Merge (Groq)
    draft = await _timed_step(
        state,
        "merge",
        merge_itinerary(
            ctx.travel_brief or {},
            ctx.artifacts.get("research", {}),
            ctx.artifacts.get("lodging", {}),
            ctx.artifacts.get("logistics", {}),
            budget_result.payload,
            limiter=limiter,
            client=groq_client if completion_fn else None,
        ),
    )
    state.write_text("draft", draft)

    # 5. Validate (Gemini)
    validator = ValidatorAgent()
    val_result = await _timed_step(
        state,
        "validator",
        validator.arun(ctx, draft, **_kwargs("validator")),
    )
    validation = val_result.payload
    state.write_json("validation", validation)

    # 6. One merge retry on fail
    if validation.get("status") == "fail":
        gaps = validation.get("gaps", [])
        draft = await _timed_step(
            state,
            "merge_retry",
            merge_itinerary(
                ctx.travel_brief or {},
                ctx.artifacts.get("research", {}),
                ctx.artifacts.get("lodging", {}),
                ctx.artifacts.get("logistics", {}),
                budget_result.payload,
                validation_gaps=gaps,
                limiter=limiter,
                client=groq_client if completion_fn else None,
            ),
        )
        state.write_text("draft", draft)
        val_result = await _timed_step(
            state,
            "validator_retry",
            validator.arun(ctx, draft, **_kwargs("validator")),
        )
        validation = val_result.payload
        state.write_json("validation", validation)

    final = _append_validation(draft, validation)
    state.write_text("final", final)

    return PlanTripResult(
        run_id=state.run_id,
        run_dir=str(state.dir),
        final_markdown=final,
        validation_status=validation.get("status", "unknown"),
        artifacts={k: str(state.dir / v) for k, v in state.ARTIFACTS.items()},
    )


def _append_validation(draft: str, validation: dict[str, Any]) -> str:
    status = validation.get("status", "unknown")
    gaps = validation.get("gaps", [])
    lines = [
        draft.rstrip(),
        "",
        "## Validation",
        f"- Status: **{status}**",
    ]
    for c in validation.get("checks", []):
        mark = "yes" if c.get("ok") else "no"
        note = f" — {c['note']}" if c.get("note") else ""
        lines.append(f"- {c.get('id', 'check')}: {mark}{note}")
    if gaps:
        lines.append("- Gaps:")
        for g in gaps:
            lines.append(f"  - [{g.get('severity', '?')}] {g.get('message', '')}")
    lines.append("")
    lines.append("*Data: LLM-only (Phase 1); not verified against live sources.*")
    return "\n".join(lines)


def plan_trip_sync(
    request: str,
    *,
    run_id: Optional[str] = None,
    completion_fn: CompletionFnOptional = None,
    runs_base_dir: Optional[Path] = None,
) -> PlanTripResult:
    return asyncio.run(
        plan_trip(
            request,
            run_id=run_id,
            completion_fn=completion_fn,
            runs_base_dir=runs_base_dir,
        )
    )
