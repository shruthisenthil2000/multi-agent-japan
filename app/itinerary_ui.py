"""Premium travel UI — profile sidebar, itinerary panel, travel actions."""

from __future__ import annotations

import html
from typing import TYPE_CHECKING, Optional

import streamlit as st

from app.conversation import ConversationManager
from app.itinerary_parser import ActivityCard, ParsedItinerary

if TYPE_CHECKING:
    from orchestrator.pipeline import PlanTripResult

# Friendly labels only — no provider or validation jargon
TRAVEL_ACTIONS = [
    ("Regenerate", "refresh the full itinerary"),
    ("More Luxury", "luxury travel style and upscale stays"),
    ("Save Money", "budget friendly options"),
    ("Add Food", "love food and local dining"),
    ("Add Nightlife", "nightlife and evening experiences"),
    ("Family Friendly", "family friendly activities"),
]

SLOT_TIME_LABELS = {
    "morning": ("🌅", "Morning"),
    "afternoon": ("🌇", "Afternoon"),
    "evening": ("🌙", "Evening"),
    "general": ("📍", "Highlights"),
}


def _budget_display(p) -> str:
    if not p.budget_amount:
        return ""
    if p.budget_currency == "INR":
        return f"₹{p.budget_amount:g}"
    return f"${p.budget_amount:g}"


def profile_completion(
    conv: ConversationManager,
    *,
    has_itinerary: bool = False,
) -> tuple[int, int, list[tuple[str, str, bool, str]]]:
    """Return (filled, total, rows) for travel profile sidebar."""
    p = conv.prefs
    dest = ", ".join(p.destinations) if p.destinations else ""
    duration = f"{p.duration_days} days" if p.duration_days else ""
    budget = _budget_display(p)
    travelers = p.companions or ""
    stay = p.travel_style or ""
    transport = "Routes planned" if has_itinerary else ""
    interests = ", ".join(p.special_preferences) if p.special_preferences else ""

    rows = [
        ("📍", "Destination", bool(dest), dest or "Where to?"),
        ("📅", "Duration", bool(duration), duration or "How long?"),
        ("💰", "Budget", bool(budget), budget or "Set a budget"),
        ("👥", "Travelers", bool(travelers), travelers or "Solo, couple…"),
        ("🏨", "Stay Type", bool(stay), stay.title() if stay else "Any style"),
        ("🚕", "Transport", bool(transport), transport or "We'll plan routes"),
        ("🎯", "Interests", bool(interests), interests or "Food, culture…"),
    ]
    filled = sum(1 for _, _, ok, _ in rows if ok)
    return filled, len(rows), rows


def render_trip_profile_sidebar(
    conv: ConversationManager,
    *,
    has_itinerary: bool = False,
) -> None:
    filled, total, rows = profile_completion(conv, has_itinerary=has_itinerary)
    pct = int(100 * filled / total) if total else 0
    bar_w = int(100 * filled / total) if total else 0

    st.markdown('<p class="trip-profile-title">Travel Profile</p>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="profile-bar"><div class="profile-bar-fill" style="width:{bar_w}%"></div></div>'
        f'<p style="font-size:0.8rem;color:#94A3B8;margin:-0.5rem 0 0.75rem;">{pct}% complete</p>',
        unsafe_allow_html=True,
    )
    for emoji, label, done, detail in rows:
        check = "✓" if done else "○"
        cls = "profile-row done" if done else "profile-row"
        safe_detail = html.escape(detail[:42] + ("…" if len(detail) > 42 else ""))
        st.markdown(
            f'<div class="{cls}"><span>{check}</span> <span class="icon">{emoji}</span> '
            f"<span><strong>{html.escape(label)}</strong><br/>"
            f'<span style="font-size:0.78rem;opacity:0.85">{safe_detail}</span></span></div>',
            unsafe_allow_html=True,
        )


def _render_activity_card_premium(card: ActivityCard, time_hint: str = "") -> None:
    title = html.escape(card.title)
    category = html.escape(card.category.replace("_", " ").title() if card.category else "Experience")
    notes = html.escape(card.notes[:200]) if card.notes else ""
    time_line = html.escape(time_hint) if time_hint else "Flexible"
    st.markdown(
        f"""<div class="activity-card-premium">
        <div class="act-title">🏯 {title}</div>
        <div class="act-meta">{time_line} · {category}</div>
        {f'<div class="act-notes">{notes}</div>' if notes else ''}
        </div>""",
        unsafe_allow_html=True,
    )


def _default_time_for_slot(slot: str, index: int) -> str:
    times = {
        "morning": ["09:00–11:00", "08:30–10:30", "10:00–12:00"],
        "afternoon": ["13:00–15:00", "14:00–16:30", "15:00–17:00"],
        "evening": ["18:00–20:00", "19:00–21:00", "17:30–19:30"],
        "general": ["Flexible", "All day", "TBD"],
    }
    opts = times.get(slot, times["general"])
    return opts[index % len(opts)]


def render_live_itinerary(parsed: ParsedItinerary, *, show_actions: bool = True) -> None:
    st.markdown('<div class="itin-panel">', unsafe_allow_html=True)
    st.markdown('<div class="itin-title">✈️ Live Itinerary</div>', unsafe_allow_html=True)

    if not parsed.has_content:
        st.markdown(
            """<div class="itin-empty">
            <p style="font-size:2rem;margin-bottom:0.5rem;">🗺️</p>
            <p>Your journey appears here</p>
            <p style="font-size:0.82rem;margin-top:0.5rem;">
            Chat with your concierge, then we'll craft your days.</p>
            </div>""",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
        return

    if parsed.summary:
        safe = html.escape(parsed.summary[:280])
        if len(parsed.summary) > 280:
            safe += "…"
        st.markdown(
            f'<p style="font-size:0.85rem;color:#94A3B8;line-height:1.5;margin-bottom:1rem;">{safe}</p>',
            unsafe_allow_html=True,
        )

    if parsed.days:
        for day in parsed.days:
            city = html.escape(day.city) if day.city else ""
            st.markdown('<div class="day-block">', unsafe_allow_html=True)
            st.markdown(
                f'<div class="day-header">Day {day.day_number}</div>'
                f'<div class="day-city">{city}</div><div class="day-divider"></div>',
                unsafe_allow_html=True,
            )
            slots = [
                ("morning", day.morning),
                ("afternoon", day.afternoon),
                ("evening", day.evening),
                ("general", day.general),
            ]
            for slot_key, cards in slots:
                if not cards:
                    continue
                emoji, label = SLOT_TIME_LABELS.get(slot_key, ("📍", "Activities"))
                st.markdown(f'<div class="slot-label">{emoji} {label}</div>', unsafe_allow_html=True)
                for i, card in enumerate(cards):
                    _render_activity_card_premium(card, _default_time_for_slot(slot_key, i))
            st.markdown("</div>", unsafe_allow_html=True)
    elif parsed.raw_markdown:
        # Fallback: strip technical sections from display
        excerpt = parsed.raw_markdown.split("## Validation")[0].split("## Day-by-day")[-1][:1200]
        st.markdown(html.escape(excerpt))

    st.markdown("</div>", unsafe_allow_html=True)


def render_travel_action_pills() -> Optional[tuple[str, str]]:
    """Render pill buttons; returns (label, suffix) if one was clicked."""
    st.markdown('<div class="pill-row">', unsafe_allow_html=True)
    cols = st.columns(3)
    for i, (label, suffix) in enumerate(TRAVEL_ACTIONS):
        with cols[i % 3]:
            if st.button(label, key=f"travel_pill_{label}", use_container_width=True):
                st.markdown("</div>", unsafe_allow_html=True)
                return (label, suffix)
    st.markdown("</div>", unsafe_allow_html=True)
    return None


def friendly_plan_ready_message() -> str:
    return (
        "Your trip is ready! I've mapped out each day on the right — "
        "take a look and tell me if you'd like any changes."
    )
