"""Startup environment validation for the Voice Travel Agent UI."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List

from app.export import reportlab_available
from app.speech import speech_recognition_available, tts_available


@dataclass
class EnvReport:
    groq_configured: bool = False
    gemini_configured: bool = False
    speech_available: bool = False
    tts_available: bool = False
    pdf_available: bool = False
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def can_run_live_plan(self) -> bool:
        return self.groq_configured and self.gemini_configured

    @property
    def has_blocking_errors(self) -> bool:
        return bool(self.errors)


def _key_set(name: str) -> bool:
    return bool(os.getenv(name, "").strip())


def check_env(*, for_live_plan: bool = True) -> EnvReport:
    report = EnvReport(
        groq_configured=_key_set("GROQ_API_KEY"),
        gemini_configured=_key_set("GEMINI_API_KEY"),
        speech_available=speech_recognition_available(),
        tts_available=tts_available(),
        pdf_available=reportlab_available(),
    )

    if for_live_plan:
        if not report.groq_configured:
            report.errors.append(
                "GROQ_API_KEY is not set. Add it to `.env` for live trip generation."
            )
        if not report.gemini_configured:
            report.errors.append(
                "GEMINI_API_KEY is not set. Add it to `.env` for budget and validation agents."
            )

    if not report.speech_available:
        report.warnings.append(
            "Voice input unavailable. Install optional deps: `pip install -e \".[voice]\"`"
        )
    if not report.tts_available:
        report.warnings.append(
            "Text-to-speech unavailable. Text chat still works fully."
        )
    if not report.pdf_available:
        report.warnings.append(
            "PDF export unavailable. Markdown export still works. "
            "Install: `pip install -e \".[voice]\"`"
        )

    return report


def render_env_sidebar(report: EnvReport, *, demo_mode: bool = False) -> None:
    """Show environment status in Streamlit sidebar."""
    import streamlit as st

    with st.sidebar:
        st.subheader("Environment")
        if demo_mode:
            st.success("Demo mode — no API keys required")
        else:
            st.markdown(
                f"Groq: {'✅' if report.groq_configured else '❌'}  \n"
                f"Gemini: {'✅' if report.gemini_configured else '❌'}"
            )
        st.markdown(
            f"Voice in: {'✅' if report.speech_available else '—'}  \n"
            f"Voice out: {'✅' if report.tts_available else '—'}  \n"
            f"PDF export: {'✅' if report.pdf_available else '—'}"
        )
        for err in report.errors:
            st.error(err)
        for warn in report.warnings:
            st.warning(warn)
