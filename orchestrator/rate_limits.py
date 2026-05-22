"""
Provider rate limits for Phase 1+ pipeline scheduling.

Values match the project's Groq / Gemini quota (see docs/implementation-plan.md).
Override via env for tier changes: GROQ_RPM, GEMINI_RPM, etc.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal, Optional

Provider = Literal["groq", "gemini"]


@dataclass(frozen=True)
class ProviderRateLimits:
    """Per-model API quotas (conservative defaults for scheduling)."""

    model: str
    requests_per_minute: int
    tokens_per_minute: int
    requests_per_day: int
    tokens_per_day: Optional[int] = None

    @property
    def min_seconds_between_requests(self) -> float:
        """Spacing to stay under RPM (with small safety margin)."""
        if self.requests_per_minute <= 0:
            return 60.0
        return max(60.0 / self.requests_per_minute, 0.5) + 0.5


# Groq — llama-3.3-70b-versatile (account limits)
GROQ_LLAMA_3_3_70B = ProviderRateLimits(
    model="llama-3.3-70b-versatile",
    requests_per_minute=30,
    tokens_per_minute=12_000,
    requests_per_day=1_000,
    tokens_per_day=100_000,
)

# Gemini — Gemini 3 Flash (free / starter tier)
GEMINI_3_FLASH = ProviderRateLimits(
    model="gemini-3-flash",
    requests_per_minute=5,
    tokens_per_minute=250_000,
    requests_per_day=20,
    tokens_per_day=None,
)


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name, "")
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def get_rate_limits(provider: Provider, model: Optional[str] = None) -> ProviderRateLimits:
    """Return limits for provider; env vars override defaults."""
    if provider == "groq":
        base = GROQ_LLAMA_3_3_70B
        return ProviderRateLimits(
            model=model or base.model,
            requests_per_minute=_int_env("GROQ_RPM", base.requests_per_minute),
            tokens_per_minute=_int_env("GROQ_TPM", base.tokens_per_minute),
            requests_per_day=_int_env("GROQ_RPD", base.requests_per_day),
            tokens_per_day=_int_env("GROQ_TPD", base.tokens_per_day or 0) or base.tokens_per_day,
        )
    base = GEMINI_3_FLASH
    return ProviderRateLimits(
        model=model or base.model,
        requests_per_minute=_int_env("GEMINI_RPM", base.requests_per_minute),
        tokens_per_minute=_int_env("GEMINI_TPM", base.tokens_per_minute),
        requests_per_day=_int_env("GEMINI_RPD", base.requests_per_day),
        tokens_per_day=None,
    )


# --- Phase 1 pipeline budget (LLM calls per successful run) ---

GROQ_CALLS_PER_RUN = {
    "intent_parser": 1,
    "destination_researcher": 1,
    "lodging": 1,
    "logistics": 1,
    "merge": 1,  # +1 on validator fail retry
}
GEMINI_CALLS_PER_RUN = {
    "budget": 1,
    "validator": 1,  # +1 if merge retry
}

GROQ_REQUESTS_PER_RUN_TYPICAL = 6  # intent + 3 parallel specialists + merge
GROQ_REQUESTS_PER_RUN_MAX = 7  # +1 merge retry
GEMINI_REQUESTS_PER_RUN_TYPICAL = 2  # budget + validator
GEMINI_REQUESTS_PER_RUN_MAX = 3  # +1 validator after retry


def estimate_runs_per_day_groq() -> int:
    return GROQ_LLAMA_3_3_70B.requests_per_day // GROQ_REQUESTS_PER_RUN_TYPICAL


def estimate_runs_per_day_gemini() -> int:
    return GEMINI_3_FLASH.requests_per_day // GEMINI_REQUESTS_PER_RUN_TYPICAL


def phase1_orchestration_rules() -> list[str]:
    """Human-readable rules enforced in Phase 1 pipeline."""
    groq = get_rate_limits("groq")
    gemini = get_rate_limits("gemini")
    return [
        f"Groq ({groq.model}): max {groq.requests_per_minute} RPM, "
        f"{groq.tokens_per_minute:,} TPM, {groq.requests_per_day:,} RPD, "
        f"{(groq.tokens_per_day or 0):,} TPD.",
        f"Gemini ({gemini.model}): max {gemini.requests_per_minute} RPM, "
        f"{gemini.tokens_per_minute:,} TPM, {gemini.requests_per_day} RPD.",
        "Run destination + lodging + logistics in parallel on Groq only (max 3 concurrent).",
        "Run budget then validator sequentially on Gemini (never parallel Gemini).",
        f"Wait >= {gemini.min_seconds_between_requests:.1f}s between Gemini calls.",
        "Keep prompts/summaries small to stay under Groq 12K TPM.",
        f"~{estimate_runs_per_day_gemini()} full demo runs/day on Gemini RPD "
        f"({GEMINI_REQUESTS_PER_RUN_TYPICAL} calls/run).",
    ]
