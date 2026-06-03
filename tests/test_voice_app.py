"""Unit tests for voice UI helpers (no LLM / no Streamlit runtime)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.conversation import ConversationManager
from app.export import export_markdown, export_pdf, reportlab_available
from app.itinerary_parser import parse_from_markdown, parse_from_run_dir, parse_itinerary
from app.speech import (
    SpeechResult,
    speech_recognition_available,
    speech_to_text,
    text_to_speech,
    tts_available,
)
from orchestrator.api import run_trip
from orchestrator.pipeline import PlanTripResult

CANONICAL = Path(__file__).resolve().parents[1] / "examples" / "canonical-japan"


# --- Conversation ---


def test_scenario_b_ready_under_amount_without_currency_symbol():
    conv = ConversationManager()
    conv.update_from_message("5 days Tokyo Kyoto under 3000")
    assert conv.is_ready_to_plan()
    req = conv.build_composed_request()
    assert "3000" in req
    assert "Tokyo" in req and "Kyoto" in req


def test_scenario_a_japan_trip_asks_required_slots_first():
    conv = ConversationManager()
    conv.update_from_message("Japan trip")
    assert conv.prefs.destinations == ["Japan"]
    assert not conv.is_ready_to_plan()
    assert conv.missing_required() == ["duration_days", "budget_amount"]
    assert "How many days" in (conv.next_clarification() or "")


def test_kyoto_to_false_positive_regression():
    conv = ConversationManager()
    conv.update_from_message("5 days Tokyo Kyoto under 3000")
    assert "trip" not in [d.lower() for d in conv.prefs.destinations]
    assert "Tokyo" in conv.prefs.destinations


def test_one_week_duration():
    conv = ConversationManager()
    conv.update_from_message("one week in Tokyo under $2000")
    assert conv.prefs.duration_days == 7
    assert conv.is_ready_to_plan()


def test_empty_input_is_noop():
    conv = ConversationManager()
    conv.update_from_message("   ")
    assert not conv.is_ready_to_plan()
    assert conv.build_composed_request  # callable
    with pytest.raises(ValueError):
        conv.build_composed_request()


def test_malformed_budget_stays_missing():
    conv = ConversationManager()
    conv.update_from_message("5 day Tokyo under $$$")
    assert conv.prefs.budget_amount is None
    assert not conv.is_ready_to_plan()


def test_multiple_destinations():
    conv = ConversationManager()
    conv.update_from_message("Paris and London 4 days $5000")
    assert conv.is_ready_to_plan()
    assert "Paris" in conv.prefs.destinations and "London" in conv.prefs.destinations


def test_readiness_gating_blocks_compose():
    conv = ConversationManager()
    conv.update_from_message("I want to visit Japan")
    assert not conv.is_ready_to_plan()
    with pytest.raises(ValueError):
        conv.build_composed_request()


def test_optional_travel_style_prompt_when_required_complete():
    conv = ConversationManager()
    conv.update_from_message("5 days Tokyo Kyoto under $3000")
    reply = conv.assistant_reply_for_turn("5 days Tokyo Kyoto under $3000")
    assert conv.is_ready_to_plan()
    assert "relaxed" in reply.lower() or "Generate trip" in reply


# --- Itinerary parser ---


def test_parse_canonical_japan_example():
    parsed = parse_from_run_dir(CANONICAL)
    assert parsed.summary
    assert len(parsed.days) >= 2


def test_research_timing_slots_when_json_present():
    parsed = parse_from_run_dir(CANONICAL)
    timed = sum(
        len(d.morning) + len(d.afternoon) + len(d.evening) for d in parsed.days
    )
    assert timed > 0


def test_parse_missing_run_dir_files_no_crash(tmp_path):
    parsed = parse_from_run_dir(tmp_path)
    assert parsed.days == []
    assert not parsed.has_content or parsed.raw_markdown == ""


def test_markdown_fallback_only():
    md = "## Summary\nFallback summary.\n\n## Day-by-day\n- Day 1: Explore."
    parsed = parse_from_markdown(md)
    assert "Fallback" in parsed.summary
    assert len(parsed.days) == 1


def test_parse_itinerary_prefers_run_dir():
    final = (CANONICAL / "08_final_itinerary.md").read_text(encoding="utf-8")
    parsed = parse_itinerary(final, str(CANONICAL))
    assert parsed.has_content


# --- Export ---


def test_export_markdown_roundtrip_unicode():
    md = "## Summary\nTokyo · ₹80000 — 東京"
    data, name = export_markdown(md, title="Test Trip")
    assert name.endswith(".md")
    assert "東京".encode("utf-8") in data


def test_export_pdf_optional():
    if not reportlab_available():
        pytest.skip("reportlab not installed")
    data, name = export_pdf("## Summary\nTest.", title="Trip")
    assert name.endswith(".pdf")
    assert len(data) > 100


def test_export_pdf_long_line():
    if not reportlab_available():
        pytest.skip("reportlab not installed")
    long_line = "A" * 5000
    data, _ = export_pdf(f"## Summary\n{long_line}", title="Long")
    assert len(data) > 100


def test_export_pdf_missing_reportlab_message():
    with patch.dict(sys.modules, {"reportlab": None, "reportlab.lib": None}):
        with patch(
            "builtins.__import__",
            side_effect=lambda name, *a, **k: (_ for _ in ()).throw(ImportError(name))
            if name.startswith("reportlab")
            else __import__(name, *a, **k),
        ):
            # Simpler: call export_pdf when reportlab import fails inside function
            pass
    try:
        import reportlab  # noqa: F401
    except ImportError:
        with pytest.raises(ImportError, match="reportlab"):
            export_pdf("## Summary\nx")


# --- Speech (mocked / missing deps) ---


def test_speech_to_text_missing_package():
    with patch("app.speech.speech_recognition_available", return_value=False):
        from app import speech

        r = speech.speech_to_text()
        assert r.error
        assert "speechrecognition" in r.error.lower()


def test_text_to_speech_missing_package():
    with patch("app.speech.tts_available", return_value=False):
        from app import speech

        err = speech.text_to_speech("hello")
        assert err and "pyttsx3" in err.lower()


def test_speech_to_text_microphone_oserror():
    with patch("app.speech.speech_recognition_available", return_value=True):
        mock_sr = MagicMock()
        mock_sr.Microphone.side_effect = OSError("Permission denied")
        mock_sr.Recognizer.return_value = MagicMock()
        with patch.dict(sys.modules, {"speech_recognition": mock_sr}):
            import importlib
            import app.speech as speech_mod

            importlib.reload(speech_mod)
            r = speech_mod.speech_to_text()
            assert r.error and "Microphone" in r.error


def test_speech_to_text_empty_transcript():
    with patch("app.speech.speech_recognition_available", return_value=True):
        mock_sr = MagicMock()
        recognizer = MagicMock()
        recognizer.recognize_google.return_value = "   "
        mock_sr.Recognizer.return_value = recognizer
        mock_sr.Microphone.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_sr.Microphone.return_value.__exit__ = MagicMock(return_value=False)
        with patch.dict(sys.modules, {"speech_recognition": mock_sr}):
            from app import speech

            r = speech.speech_to_text()
            assert r.error and "Empty" in r.error


# --- API wrapper ---


def test_run_trip_delegates_to_plan_trip_sync():
    fake = PlanTripResult(
        run_id="test123",
        run_dir="/tmp/runs/test123",
        final_markdown="## Summary\nDone.",
        validation_status="pass",
        artifacts={},
    )
    with patch("orchestrator.api.plan_trip_sync", return_value=fake) as mock_sync:
        out = run_trip("Plan a 5-day Tokyo trip under $3000")
        mock_sync.assert_called_once()
        assert out.run_id == "test123"
        assert out.final_markdown.startswith("## Summary")


# --- Packaging smoke ---


def test_app_package_imports():
    import app  # noqa: F401
    import app.conversation
    import app.export
    import app.itinerary_parser
    import app.speech
