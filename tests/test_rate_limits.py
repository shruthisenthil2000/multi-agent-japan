import pytest

from llm.rate_limiter import ProviderRateLimiter, RateLimitExceeded
from orchestrator.rate_limits import (
    GEMINI_3_FLASH,
    GEMINI_REQUESTS_PER_RUN_TYPICAL,
    GROQ_LLAMA_3_3_70B,
    GROQ_REQUESTS_PER_RUN_TYPICAL,
    estimate_runs_per_day_gemini,
    estimate_runs_per_day_groq,
    phase1_orchestration_rules,
)


def test_groq_limits_defaults():
    assert GROQ_LLAMA_3_3_70B.requests_per_minute == 30
    assert GROQ_LLAMA_3_3_70B.tokens_per_minute == 12_000
    assert GROQ_LLAMA_3_3_70B.requests_per_day == 1_000
    assert GROQ_LLAMA_3_3_70B.tokens_per_day == 100_000


def test_gemini_limits_defaults():
    assert GEMINI_3_FLASH.requests_per_minute == 5
    assert GEMINI_3_FLASH.tokens_per_minute == 250_000
    assert GEMINI_3_FLASH.requests_per_day == 20
    assert GEMINI_3_FLASH.min_seconds_between_requests >= 12.0


def test_estimated_runs_per_day():
    assert estimate_runs_per_day_groq() == 1000 // GROQ_REQUESTS_PER_RUN_TYPICAL
    assert estimate_runs_per_day_gemini() == 20 // GEMINI_REQUESTS_PER_RUN_TYPICAL


def test_phase1_rules_mention_gemini_sequential():
    rules = phase1_orchestration_rules()
    text = " ".join(rules).lower()
    assert "sequential" in text or "never parallel" in text
    assert "gemini" in text


def test_daily_quota_exceeded(tmp_path):
    limiter = ProviderRateLimiter(
        usage_dir=tmp_path / "quota",
        gemini_model="gemini-3-flash",
    )
    usage_file = limiter._usage_file("gemini")
    usage_file.parent.mkdir(parents=True, exist_ok=True)
    usage_file.write_text('{"requests": 20}')

    with pytest.raises(RateLimitExceeded) as exc:
        limiter.check_daily_quota("gemini")
    assert exc.value.limit == 20
