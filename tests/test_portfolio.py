"""Tests for Phase 4 portfolio modules (no API / no Streamlit runtime)."""

from pathlib import Path

import pytest

from app.demo_data import (
    canonical_example_available,
    demo_request_text,
    load_demo_result,
)
from app.env_check import check_env
from app.progress import (
    STAGE_MESSAGES,
    load_trace,
    progress_fraction,
    stage_message_from_trace,
)

CANONICAL = Path(__file__).resolve().parents[1] / "examples" / "canonical-japan"


def test_demo_loads_without_api():
    assert canonical_example_available()
    result = load_demo_result()
    assert result.run_id
    assert "Summary" in result.final_markdown or "##" in result.final_markdown
    assert result.validation_status
    assert Path(result.run_dir).exists()


def test_demo_request_text_non_empty():
    assert len(demo_request_text()) > 10


def test_trace_load_canonical():
    entries = load_trace(CANONICAL)
    assert len(entries) >= 5
    assert entries[0].step == "intent_parser"


def test_stage_message_from_trace():
    entries = load_trace(CANONICAL)
    msg = stage_message_from_trace(entries)
    assert msg in STAGE_MESSAGES or msg == "Starting pipeline..."


def test_progress_fraction_bounds():
    entries = load_trace(CANONICAL)
    assert 0.0 < progress_fraction(entries) <= 1.0


def test_trace_missing_dir():
    assert load_trace("/nonexistent/path") == []


def test_env_check_structure(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    report = check_env(for_live_plan=True)
    assert not report.can_run_live_plan
    assert len(report.errors) >= 2
