"""Pipeline integration tests — mock LLM only (no API keys / quota)."""

import json
from pathlib import Path

import pytest

from orchestrator.config import AGENT_PROVIDERS, get_settings
from orchestrator.pipeline import plan_trip_sync

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def disable_rate_limit(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    get_settings.cache_clear()


def test_plan_trip_e2e_mock(
    mock_completion_fn, canonical_request, disable_rate_limit, tmp_path
):
    result = plan_trip_sync(
        canonical_request,
        run_id="test-run",
        completion_fn=mock_completion_fn,
        runs_base_dir=tmp_path / "runs",
    )
    assert result.run_id == "test-run"
    run_dir = Path(result.run_dir)
    assert (run_dir / "01_travel_brief.json").exists()
    assert (run_dir / "08_final_itinerary.md").exists()

    brief = json.loads((run_dir / "01_travel_brief.json").read_text())
    assert brief["duration_days"] == 5
    assert brief["destinations"][0]["city"] == "Tokyo"

    final = result.final_markdown
    assert "## Summary" in final
    assert "## Day-by-day" in final
    assert "## Where to stay" in final
    assert "## Logistics" in final
    assert "## Budget" in final or "## Budget notes" in final
    assert "## Validation" in final
    assert "temple" in final.lower() or "food" in final.lower()

    trace_lines = (run_dir / "trace.jsonl").read_text().strip().split("\n")
    steps = [json.loads(line)["step"] for line in trace_lines if line]
    assert "intent_parser" in steps
    assert "budget" in steps
    assert "validator" in steps
    assert len(trace_lines) >= 6


def test_plan_trip_rejects_empty(disable_rate_limit):
    with pytest.raises(ValueError, match="required"):
        plan_trip_sync("   ")


def test_agent_providers_two_brain():
    assert AGENT_PROVIDERS["budget"] == "gemini"
    assert AGENT_PROVIDERS["validator"] == "gemini"
    assert AGENT_PROVIDERS["destination_researcher"] == "groq"
    assert AGENT_PROVIDERS["lodging"] == "groq"
    assert AGENT_PROVIDERS["logistics"] == "groq"
    assert AGENT_PROVIDERS["merge"] == "groq"


def test_all_artifacts_written(mock_completion_fn, canonical_request, disable_rate_limit, tmp_path):
    result = plan_trip_sync(
        canonical_request,
        run_id="artifacts-check",
        completion_fn=mock_completion_fn,
        runs_base_dir=tmp_path / "runs",
    )
    run_dir = Path(result.run_dir)
    for key in (
        "00_request.txt",
        "01_travel_brief.json",
        "02_research.json",
        "03_lodging.json",
        "04_logistics.json",
        "05_budget.json",
        "06_draft_itinerary.md",
        "07_validation.json",
        "08_final_itinerary.md",
        "trace.jsonl",
    ):
        assert (run_dir / key).exists(), key
