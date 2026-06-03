"""Parse pipeline outputs into UI-friendly structures."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class ActivityCard:
    title: str
    category: str = "activity"
    duration: str = ""
    notes: str = ""
    location: str = ""
    time_of_day: str = "general"  # morning | afternoon | evening | general


@dataclass
class DayPlan:
    day_number: int
    label: str
    city: str = ""
    summary: str = ""
    morning: list[ActivityCard] = field(default_factory=list)
    afternoon: list[ActivityCard] = field(default_factory=list)
    evening: list[ActivityCard] = field(default_factory=list)
    general: list[ActivityCard] = field(default_factory=list)


@dataclass
class ParsedItinerary:
    summary: str = ""
    days: list[DayPlan] = field(default_factory=list)
    stay: str = ""
    logistics: str = ""
    budget_notes: str = ""
    validation: str = ""
    raw_markdown: str = ""

    @property
    def has_content(self) -> bool:
        return bool(self.summary or self.days or self.stay or self.raw_markdown)


_TIMING_MAP = {
    "early_morning": "morning",
    "morning": "morning",
    "afternoon": "afternoon",
    "evening": "evening",
    "off_peak": "evening",
}


def _timing_to_slot(timing: str) -> str:
    return _TIMING_MAP.get(timing.lower().replace(" ", "_"), "general")


def _extract_section(md: str, heading: str) -> str:
    pattern = rf"##\s*{re.escape(heading)}\s*\n(.*?)(?=\n##\s|\Z)"
    m = re.search(pattern, md, re.I | re.S)
    return m.group(1).strip() if m else ""


def parse_from_markdown(markdown: str) -> ParsedItinerary:
    md = markdown.strip()
    out = ParsedItinerary(raw_markdown=md)
    out.summary = _extract_section(md, "Summary")
    out.stay = _extract_section(md, "Where to stay")
    out.logistics = _extract_section(md, "Logistics")
    out.budget_notes = _extract_section(md, "Budget notes") or _extract_section(md, "Budget")
    out.validation = _extract_section(md, "Validation")

    day_block = _extract_section(md, "Day-by-day")
    if day_block:
        out.days = _parse_day_bullets(day_block)
    return out


def _parse_day_bullets(block: str) -> list[DayPlan]:
    days: list[DayPlan] = []
    for i, line in enumerate(block.splitlines(), start=1):
        line = line.strip()
        if not line.startswith("-"):
            continue
        m = re.match(r"^-\s*Day\s*(\d+)\s*[:\-—]\s*(.+)$", line, re.I)
        if m:
            day_num = int(m.group(1))
            rest = m.group(2).strip()
            city = ""
            cm = re.match(r"^([^,]+?)(?:,|\s+—)", rest)
            if cm:
                city = cm.group(1).strip()
            card = ActivityCard(title=rest, notes=rest, location=city or rest)
            days.append(
                DayPlan(
                    day_number=day_num,
                    label=f"Day {day_num}",
                    city=city,
                    summary=rest,
                    general=[card],
                )
            )
        elif days:
            days[-1].summary += " " + line.lstrip("- ").strip()
    return days


def parse_from_run_dir(run_dir: Path) -> ParsedItinerary:
    run_dir = Path(run_dir)
    final_path = run_dir / "08_final_itinerary.md"
    if final_path.exists():
        parsed = parse_from_markdown(final_path.read_text(encoding="utf-8"))
    else:
        parsed = ParsedItinerary()

    research_path = run_dir / "02_research.json"
    research = _load_json(research_path)
    if research and research.get("cities"):
        # Prefer structured research for day cards (Morning/Afternoon/Evening).
        parsed.days = []
        parsed = _enrich_from_research(parsed, research_path)

    parsed = _enrich_from_brief(parsed, run_dir / "01_travel_brief.json")
    return parsed


def _load_json(path: Path) -> Optional[dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _enrich_from_brief(parsed: ParsedItinerary, path: Path) -> ParsedItinerary:
    data = _load_json(path)
    if not data:
        return parsed
    if not parsed.summary:
        dests = ", ".join(d.get("city", "") for d in data.get("destinations", []))
        parsed.summary = (
            f"{data.get('duration_days', '?')} days — {dests}. "
            f"Budget: {data.get('budget', {}).get('amount', '?')} "
            f"{data.get('budget', {}).get('currency', '')}"
        )
    return parsed


def _enrich_from_research(parsed: ParsedItinerary, path: Path) -> ParsedItinerary:
    data = _load_json(path)
    if not data:
        return parsed
    cities = data.get("cities", {})
    day_num = 1
    for city, block in cities.items():
        activities = block.get("activities", [])
        if not activities:
            continue
        day = DayPlan(day_number=day_num, label=f"Day {day_num}", city=city)
        for act in activities[:4]:
            slot = _timing_to_slot(act.get("suggested_timing", "general"))
            card = ActivityCard(
                title=act.get("name", "Activity"),
                category=act.get("type", "activity"),
                notes=act.get("why", ""),
                location=city,
                time_of_day=slot,
            )
            if slot == "morning":
                day.morning.append(card)
            elif slot == "afternoon":
                day.afternoon.append(card)
            elif slot == "evening":
                day.evening.append(card)
            else:
                day.general.append(card)
        if not (day.morning or day.afternoon or day.evening):
            day.general = [
                ActivityCard(
                    title=a.get("name", ""),
                    category=a.get("type", ""),
                    notes=a.get("why", ""),
                    location=city,
                )
                for a in activities[:3]
            ]
        parsed.days.append(day)
        day_num += 1
    return parsed


def parse_itinerary(
    final_markdown: str,
    run_dir: Optional[str] = None,
) -> ParsedItinerary:
    """Prefer run_dir JSON enrichment; fall back to markdown-only."""
    if run_dir:
        enriched = parse_from_run_dir(Path(run_dir))
        if enriched.has_content:
            if not enriched.raw_markdown and final_markdown:
                enriched.raw_markdown = final_markdown
            return enriched
    return parse_from_markdown(final_markdown)
