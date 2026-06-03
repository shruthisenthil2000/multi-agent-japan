"""
Problem-statement acceptance checks against golden example (no LLM calls).

Run: pytest tests/test_acceptance.py
"""

import json
from pathlib import Path

import pytest

GOLDEN_DIR = Path(__file__).parent.parent / "examples" / "canonical-japan"


@pytest.fixture
def golden_dir():
    if not (GOLDEN_DIR / "08_final_itinerary.md").exists():
        pytest.skip("Golden example missing — copy from runs/ per Phase 2.3")
    return GOLDEN_DIR


def test_golden_artifacts_present(golden_dir):
    required = [
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
    ]
    for name in required:
        assert (golden_dir / name).is_file(), f"Missing {name}"


def test_acceptance_travel_brief(golden_dir):
    brief = json.loads((golden_dir / "01_travel_brief.json").read_text())
    assert brief["duration_days"] == 5
    cities = [d["city"] for d in brief["destinations"]]
    assert "Tokyo" in cities and "Kyoto" in cities


def test_acceptance_final_itinerary_sections(golden_dir):
    final = (golden_dir / "08_final_itinerary.md").read_text().lower()
    for section in ("summary", "day-by-day", "where to stay", "logistics", "budget", "validation"):
        assert section in final


def test_acceptance_preferences_referenced(golden_dir):
    final = (golden_dir / "08_final_itinerary.md").read_text().lower()
    assert "food" in final or "sushi" in final or "market" in final
    assert "temple" in final or "shrine" in final
    assert "crowd" in final or "early morning" in final


def test_acceptance_validation_status(golden_dir):
    report = json.loads((golden_dir / "07_validation.json").read_text())
    assert report["status"] in ("pass", "pass_with_gaps")


def test_acceptance_trace_min_steps(golden_dir):
    lines = (golden_dir / "trace.jsonl").read_text().strip().split("\n")
    steps = {json.loads(line)["step"] for line in lines if line}
    for required in ("intent_parser", "budget", "validator", "merge"):
        assert required in steps
    assert len(lines) >= 6
