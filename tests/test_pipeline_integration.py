import json
from pathlib import Path

import pytest

from orchestrator.config import get_settings
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


def test_plan_trip_rejects_empty(disable_rate_limit):
    with pytest.raises(ValueError, match="required"):
        plan_trip_sync("   ")


def test_agent_providers():
    from orchestrator.config import AGENT_PROVIDERS

    assert AGENT_PROVIDERS["budget"] == "gemini"
    assert AGENT_PROVIDERS["destination_researcher"] == "groq"
