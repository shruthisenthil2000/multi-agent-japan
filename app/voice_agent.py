"""
Premium AI Travel Concierge — Streamlit UI.

Run: streamlit run app/voice_agent.py
"""

from __future__ import annotations

import html
import threading
import time
import uuid
from pathlib import Path
from typing import Any

import streamlit as st
from dotenv import load_dotenv

from app.conversation import ConversationManager, TravelPreferences
from app.env_check import check_env
from app.export import export_markdown, export_pdf, reportlab_available
from app.itinerary_parser import ParsedItinerary, parse_itinerary
from app.itinerary_ui import (
    friendly_plan_ready_message,
    render_live_itinerary,
    render_travel_action_pills,
    render_trip_profile_sidebar,
)
from app.progress import load_trace, progress_fraction, stage_message_from_trace
from app.speech import speech_to_text, text_to_speech, tts_available
from app.theme import CHAT_SCROLL_JS, PREMIUM_CSS
from orchestrator.api import run_trip

load_dotenv()

st.set_page_config(
    page_title="Travel Concierge",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(PREMIUM_CSS, unsafe_allow_html=True)


def _init_session() -> None:
    defaults: dict[str, Any] = {
        "messages": [],
        "prefs": TravelPreferences(),
        "conversation": None,
        "plan_result": None,
        "parsed_itinerary": None,
        "is_planning": False,
        "ui_overlay": None,
        "overlay_subtitle": "",
        "pending_prompt": None,
        "tts_enabled": True,
        "_do_listen": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    if st.session_state.conversation is None:
        st.session_state.conversation = ConversationManager(st.session_state.prefs)


def _render_overlay() -> None:
    mode = st.session_state.get("ui_overlay")
    if not mode:
        return
    sub = html.escape(st.session_state.get("overlay_subtitle", ""))
    if mode == "listening":
        inner = (
            '<div class="pulse-ring"></div>'
            '<div class="ui-modal-icon">🎤</div>'
            '<div class="ui-modal-title">Listening…</div>'
            f'<div class="ui-modal-sub">{sub or "Tell me about your dream trip"}</div>'
        )
    elif mode == "planning":
        inner = (
            '<div class="loader-spin"></div>'
            '<div class="ui-modal-icon">🧠</div>'
            '<div class="ui-modal-title">Planning your trip…</div>'
            f'<div class="ui-modal-sub">{sub or "Crafting the perfect days for you"}</div>'
        )
    elif mode == "speaking":
        inner = (
            '<div class="pulse-ring"></div>'
            '<div class="ui-modal-icon">🔊</div>'
            '<div class="ui-modal-title">Reading aloud…</div>'
            '<div class="ui-modal-sub">Your itinerary summary</div>'
        )
    else:
        return
    st.markdown(
        f'<div class="ui-overlay"><div class="ui-modal">{inner}</div></div>',
        unsafe_allow_html=True,
    )


def _render_message(role: str, content: str) -> None:
    safe = html.escape(content).replace("\n", "<br/>")
    if role == "user":
        st.markdown(
            f'<div class="msg-row user"><div class="msg-user">{safe}</div></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="msg-row"><div class="msg-assistant">{safe}</div></div>',
            unsafe_allow_html=True,
        )


def _render_typing() -> None:
    st.markdown(
        """<div class="msg-row"><div class="msg-assistant">
        <span class="typing-dots"><span></span><span></span><span></span></span>
        </div></div>""",
        unsafe_allow_html=True,
    )


def _user_friendly_error(err: Exception) -> str:
    text = str(err).lower()
    if "api" in text or "key" in text or "auth" in text:
        return (
            "I couldn't connect to our planning service. "
            "Please make sure everything is set up, then try again."
        )
    return "Something went wrong while planning. Please try again in a moment."


def _run_planner(composed: str) -> None:
    run_id = uuid.uuid4().hex[:12]
    runs_base = Path("runs")
    trace_dir = runs_base / run_id
    result_holder: dict[str, Any] = {}
    error_holder: dict[str, Exception] = {}

    def worker() -> None:
        try:
            result_holder["result"] = run_trip(
                composed, run_id=run_id, runs_base_dir=runs_base
            )
        except Exception as e:
            error_holder["error"] = e

    st.session_state.is_planning = True
    st.session_state.ui_overlay = "planning"
    st.session_state.overlay_subtitle = "Finding the best experiences for you"
    _render_overlay()

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    while thread.is_alive():
        entries = load_trace(trace_dir)
        sub = stage_message_from_trace(entries)
        friendly = {
            "Parsing request...": "Understanding your preferences…",
            "Running specialists...": "Exploring destinations & stays…",
            "Merging itinerary...": "Shaping your day-by-day plan…",
            "Validating plan...": "Adding finishing touches…",
        }
        st.session_state.overlay_subtitle = friendly.get(sub, "Crafting your journey…")
        _render_overlay()
        time.sleep(0.45)

    thread.join(timeout=1.0)
    st.session_state.is_planning = False
    st.session_state.ui_overlay = None

    if "error" in error_holder:
        st.session_state.messages.append(
            {"role": "assistant", "content": _user_friendly_error(error_holder["error"])}
        )
        return

    result = result_holder["result"]
    st.session_state.plan_result = result
    st.session_state.parsed_itinerary = parse_itinerary(
        result.final_markdown, result.run_dir
    )
    st.session_state.messages.append(
        {"role": "assistant", "content": friendly_plan_ready_message()}
    )


def _handle_send(conv: ConversationManager, text: str, *, try_plan: bool = False) -> None:
    text = text.strip()
    if not text:
        return
    st.session_state.messages.append({"role": "user", "content": text})
    plan_phrases = ("plan my trip", "create itinerary", "generate trip", "book it", "plan it")
    wants_plan = try_plan or any(p in text.lower() for p in plan_phrases)

    if wants_plan and conv.is_ready_to_plan():
        env = check_env(for_live_plan=True)
        if not env.can_run_live_plan:
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": (
                        "I'd love to build your itinerary, but trip planning isn't "
                        "available right now. Please check your configuration and try again."
                    ),
                }
            )
            return
        _run_planner(conv.build_composed_request())
        return

    reply = conv.assistant_reply_for_turn(text).replace("**", "")
    st.session_state.messages.append({"role": "assistant", "content": reply})
    if st.session_state.tts_enabled and tts_available():
        st.session_state.ui_overlay = "speaking"
        _render_overlay()
        text_to_speech(reply)
        st.session_state.ui_overlay = None


def _apply_pending_prompt(conv: ConversationManager) -> None:
    prompt = st.session_state.pop("pending_prompt", None)
    if prompt:
        _handle_send(conv, prompt)


def _reset_conversation() -> None:
    st.session_state.messages = []
    st.session_state.prefs = TravelPreferences()
    st.session_state.conversation = ConversationManager()
    st.session_state.plan_result = None
    st.session_state.parsed_itinerary = None


def _travel_action(conv: ConversationManager, label: str, suffix: str) -> None:
    if label != "Regenerate":
        conv.update_from_message(suffix)
    if not conv.is_ready_to_plan():
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": "Tell me a bit more about your trip first — destination, length, and budget.",
            }
        )
        return
    env = check_env(for_live_plan=True)
    if not env.can_run_live_plan:
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": "I can't update the itinerary right now. Please try again shortly.",
            }
        )
        return
    st.session_state.messages.append(
        {"role": "user", "content": f"Please {suffix}"}
    )
    _run_planner(conv.build_composed_request())


def _process_voice_listen(conv: ConversationManager) -> None:
    st.session_state.ui_overlay = "listening"
    _render_overlay()
    result = speech_to_text()
    st.session_state.ui_overlay = None
    if result.error:
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": "I didn't catch that. Could you try again or type your message?",
            }
        )
    elif result.text:
        st.session_state.overlay_subtitle = result.text
        _handle_send(conv, result.text)


def main() -> None:
    _init_session()
    conv: ConversationManager = st.session_state.conversation

    if st.session_state.pop("_do_listen", False):
        _process_voice_listen(conv)
        st.rerun()

    _apply_pending_prompt(conv)
    _render_overlay()

    with st.sidebar:
        render_trip_profile_sidebar(
            conv, has_itinerary=bool(st.session_state.plan_result)
        )
        st.markdown("<br/>", unsafe_allow_html=True)
        if st.button("Start over", use_container_width=True):
            _reset_conversation()
            st.rerun()
        st.markdown(
            '<p class="trip-profile-title" style="margin-top:1.5rem">Try saying</p>',
            unsafe_allow_html=True,
        )
        for i, s in enumerate(
            [
                "5-day Tokyo & Kyoto under $3000, food & culture",
                "One week in Paris, $5000, romantic getaway",
            ]
        ):
            if st.button(s, key=f"starter_{i}", use_container_width=True):
                st.session_state.pending_prompt = s
                st.rerun()

    chat_col, itin_col = st.columns([1.65, 1], gap="medium")

    with chat_col:
        st.markdown(
            '<div class="chat-header">AI Travel Assistant</div>'
            '<div class="chat-sub">Your personal concierge for dream itineraries</div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="chat-scroll">', unsafe_allow_html=True)
        if not st.session_state.messages:
            st.markdown(
                """<div class="msg-row"><div class="msg-assistant">
                Welcome! I'm your travel concierge. Share where you'd like to go,
                how long you're staying, and your budget — by voice or text.
                I'll handle the rest.
                </div></div>""",
                unsafe_allow_html=True,
            )
        for msg in st.session_state.messages:
            _render_message(msg["role"], msg["content"])
        if st.session_state.is_planning and not st.session_state.ui_overlay:
            _render_typing()
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown(CHAT_SCROLL_JS, unsafe_allow_html=True)

        ready = conv.is_ready_to_plan()

        st.markdown('<div class="composer-wrap"><div class="composer-shell">', unsafe_allow_html=True)
        with st.form("composer", clear_on_submit=True):
            user_text = st.text_area(
                "composer_input",
                placeholder="Ask about your trip…",
                label_visibility="collapsed",
                height=72,
            )
            st.markdown('<div class="composer-actions">', unsafe_allow_html=True)
            c1, c2, c3 = st.columns([1, 1, 6])
            with c1:
                mic = st.form_submit_button("🎤", help="Voice input")
            with c2:
                plan_btn = st.form_submit_button(
                    "✨",
                    help="Create your itinerary" if ready else "Complete your travel profile first",
                    disabled=not ready or st.session_state.is_planning,
                )
            with c3:
                send = st.form_submit_button("➤", type="primary", help="Send")
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div></div>", unsafe_allow_html=True)

        if mic:
            st.session_state._do_listen = True
            st.rerun()

        if send and user_text and user_text.strip():
            _handle_send(conv, user_text.strip())
            st.rerun()

        if plan_btn and ready:
            env = check_env(for_live_plan=True)
            st.session_state.messages.append(
                {"role": "user", "content": "Please create my itinerary"}
            )
            if env.can_run_live_plan:
                _run_planner(conv.build_composed_request())
            else:
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": (
                            "I'd love to plan your trip, but the service isn't "
                            "available right now. Please check your setup."
                        ),
                    }
                )
            st.rerun()

        if ready and not st.session_state.plan_result:
            st.markdown(
                '<p style="text-align:center;font-size:0.8rem;color:#64748b;margin-top:0.5rem;">'
                "Profile complete — tap ✨ to create your itinerary</p>",
                unsafe_allow_html=True,
            )

    with itin_col:
        result = st.session_state.plan_result
        parsed = st.session_state.parsed_itinerary

        if result and parsed:
            render_live_itinerary(parsed)
            action = render_travel_action_pills()
            if action:
                _travel_action(conv, action[0], action[1])
                st.rerun()
            d1, d2 = st.columns(2)
            with d1:
                md_bytes, md_name = export_markdown(result.final_markdown, title="my-trip")
                st.download_button(
                    "Download",
                    data=md_bytes,
                    file_name=md_name,
                    mime="text/markdown",
                    use_container_width=True,
                )
            with d2:
                if reportlab_available():
                    try:
                        pdf_bytes, pdf_name = export_pdf(
                            result.final_markdown, title="My Trip"
                        )
                        st.download_button(
                            "PDF",
                            data=pdf_bytes,
                            file_name=pdf_name,
                            mime="application/pdf",
                            use_container_width=True,
                        )
                    except Exception:
                        pass
        else:
            render_live_itinerary(ParsedItinerary())


if __name__ == "__main__":
    main()
