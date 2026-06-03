"""Conversational slot-filling before invoking plan_trip_sync."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class TravelPreferences:
    destinations: list[str] = field(default_factory=list)
    duration_days: Optional[int] = None
    budget_amount: Optional[float] = None
    budget_currency: str = "USD"
    travel_style: Optional[str] = None
    companions: Optional[str] = None
    special_preferences: list[str] = field(default_factory=list)
    anti_preferences: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "destinations": self.destinations,
            "duration_days": self.duration_days,
            "budget_amount": self.budget_amount,
            "budget_currency": self.budget_currency,
            "travel_style": self.travel_style,
            "companions": self.companions,
            "special_preferences": self.special_preferences,
            "anti_preferences": self.anti_preferences,
        }


REQUIRED_SLOTS = ("destinations", "duration_days", "budget_amount")

CLARIFICATION_PROMPTS = {
    "destinations": "What destination or cities are you planning to visit?",
    "duration_days": "How many days is your trip?",
    "budget_amount": "What is your approximate total budget (e.g. $3000 or ₹80000)?",
    "travel_style": "Do you prefer a relaxed, balanced, or packed itinerary?",
    "companions": "Who are you traveling with — solo, couple, friends, or family?",
    "special_preferences": "Any must-haves? (e.g. food, temples, anime, nightlife)",
}


class ConversationManager:
    """Rule-based slot filling for MVP (no extra LLM calls during chat)."""

    def __init__(self, prefs: Optional[TravelPreferences] = None) -> None:
        self.prefs = prefs or TravelPreferences()

    def update_from_message(self, text: str) -> None:
        t = text.strip()
        if not t:
            return
        self._extract_destinations(t)
        self._extract_duration(t)
        self._extract_budget(t)
        self._extract_companions(t)
        self._extract_style(t)
        self._extract_preferences(t)

    def missing_required(self) -> list[str]:
        missing = []
        if not self.prefs.destinations:
            missing.append("destinations")
        if not self.prefs.duration_days:
            missing.append("duration_days")
        if not self.prefs.budget_amount:
            missing.append("budget_amount")
        return missing

    def missing_optional(self) -> list[str]:
        optional = []
        if not self.prefs.travel_style:
            optional.append("travel_style")
        if not self.prefs.companions:
            optional.append("companions")
        if not self.prefs.special_preferences:
            optional.append("special_preferences")
        return optional

    def is_ready_to_plan(self) -> bool:
        return len(self.missing_required()) == 0

    def next_clarification(self) -> Optional[str]:
        missing = self.missing_required()
        if missing:
            return CLARIFICATION_PROMPTS[missing[0]]
        optional = self.missing_optional()
        if optional:
            return CLARIFICATION_PROMPTS.get(optional[0])
        return None

    def assistant_reply_for_turn(self, user_text: str) -> str:
        """Update slots and return the next assistant message."""
        self.update_from_message(user_text)
        if self.is_ready_to_plan():
            optional = self.missing_optional()
            if optional:
                key = optional[0]
                return (
                    f"Great — I have enough to start planning. "
                    f"{CLARIFICATION_PROMPTS[key]} "
                    "(Optional — you can also click **Generate trip** now.)"
                )
            return (
                "I have everything I need. Click **Generate trip** when you're ready, "
                "or add more preferences in chat."
            )
        return self.next_clarification() or "Tell me more about your trip."

    def build_composed_request(self) -> str:
        if not self.is_ready_to_plan():
            raise ValueError("Cannot compose request: required slots missing")

        p = self.prefs
        dest = " + ".join(p.destinations)
        parts = [f"Plan a {p.duration_days}-day trip to {dest}"]

        if p.companions:
            parts.append(f"for {p.companions}")
        if p.budget_amount:
            sym = "$" if p.budget_currency == "USD" else ""
            if p.budget_currency == "INR":
                sym = "₹"
            parts.append(f"under {sym}{p.budget_amount:g} budget")
        if p.travel_style:
            parts.append(f"{p.travel_style} pace")
        if p.special_preferences:
            parts.append(f"love {', '.join(p.special_preferences)}")
        if p.anti_preferences:
            parts.append(f"hate {', '.join(p.anti_preferences)}")

        return ". ".join(parts) + "."

    def _extract_destinations(self, text: str) -> None:
        if self.prefs.destinations:
            return
        known = re.findall(
            r"\b(Tokyo|Kyoto|Osaka|Jaipur|Delhi|Paris|London|Bali|Bangkok|Singapore|Rome|Barcelona|Japan|India)\b",
            text,
            re.I,
        )
        if known:
            self.prefs.destinations = list(dict.fromkeys(c.title() for c in known))
            return
        # "trip to Tokyo", "visit Kyoto and Osaka" — word-boundary prepositions only
        m = re.search(
            r"(?:^|\s)(?:to|visit|in)\s+([A-Za-z][A-Za-z\s,\+&]+?)(?:\.|,| for | with | under |\$|₹|\d+\s*day)",
            text,
            re.I,
        )
        if m:
            chunk = m.group(1).strip()
            if chunk.lower() not in ("trip", "a", "the"):
                cities = re.split(r"\s*(?:,|\+|&| and )\s*", chunk)
                self.prefs.destinations = [c.strip() for c in cities if c.strip()]

    def _extract_duration(self, text: str) -> None:
        if self.prefs.duration_days:
            return
        if re.search(r"\b(?:one|a)\s+week\b", text, re.I):
            self.prefs.duration_days = 7
            return
        m = re.search(r"(\d+)\s*[- ]?\s*weeks?", text, re.I)
        if m:
            self.prefs.duration_days = int(m.group(1)) * 7
            return
        m = re.search(r"(\d+)\s*[- ]?\s*day", text, re.I)
        if m:
            self.prefs.duration_days = int(m.group(1))

    def _extract_budget(self, text: str) -> None:
        if self.prefs.budget_amount:
            return
        m = re.search(
            r"(?:under|below|max|up to|less than)\s*[\$₹]?\s*([\d,]+(?:\.\d+)?)\s*(k|K)?",
            text,
            re.I,
        )
        if m:
            val = float(m.group(1).replace(",", ""))
            if m.group(2):
                val *= 1000
            self.prefs.budget_amount = val
            if "₹" in text:
                self.prefs.budget_currency = "INR"
            return
        m = re.search(r"₹\s*([\d,]+(?:\.\d+)?)\s*(k|K)?", text)
        if m:
            val = float(m.group(1).replace(",", ""))
            if m.group(2):
                val *= 1000
            self.prefs.budget_amount = val
            self.prefs.budget_currency = "INR"
            return
        m = re.search(r"\$\s*([\d,]+(?:\.\d+)?)\s*(k|K)?", text)
        if m:
            val = float(m.group(1).replace(",", ""))
            if m.group(2):
                val *= 1000
            self.prefs.budget_amount = val
            self.prefs.budget_currency = "USD"
            return
        m = re.search(r"budget\s*(?:of|around|about)?\s*([\d,]+)", text, re.I)
        if m:
            self.prefs.budget_amount = float(m.group(1).replace(",", ""))

    def _extract_companions(self, text: str) -> None:
        if self.prefs.companions:
            return
        for label, phrase in (
            ("solo", "solo"),
            ("couple", "a couple"),
            ("friends", "friends"),
            ("family", "family"),
        ):
            if re.search(rf"\b{label}\b", text, re.I):
                self.prefs.companions = phrase
                return
        m = re.search(r"for\s+(\d+)\s+people", text, re.I)
        if m:
            n = int(m.group(1))
            self.prefs.companions = f"{n} people"

    def _extract_style(self, text: str) -> None:
        if self.prefs.travel_style:
            return
        for style in ("relaxed", "balanced", "packed", "moderate", "luxury", "budget"):
            if re.search(rf"\b{style}\b", text, re.I):
                self.prefs.travel_style = style
                return

    def _extract_preferences(self, text: str) -> None:
        t = text.lower()
        keywords = {
            "food": ["food", "sushi", "ramen", "street food", "dining"],
            "temples": ["temple", "temples", "shrine"],
            "anime": ["anime", "manga"],
            "nightlife": ["nightlife", "bars", "clubs"],
            "nature": ["nature", "hiking", "parks"],
            "culture": ["culture", "museums", "history"],
        }
        for pref, triggers in keywords.items():
            if any(tr in t for tr in triggers) and pref not in self.prefs.special_preferences:
                self.prefs.special_preferences.append(pref)
        if re.search(r"hate crowds|avoid crowds|no crowds", t):
            if "crowds" not in self.prefs.anti_preferences:
                self.prefs.anti_preferences.append("crowds")
