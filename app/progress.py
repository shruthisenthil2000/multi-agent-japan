"""Read and visualize pipeline trace.jsonl without modifying orchestration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

# User-facing stage messages (UI only; pipeline unchanged).
STAGE_MESSAGES = (
    "Parsing request...",
    "Running specialists...",
    "Merging itinerary...",
    "Validating plan...",
)

STEP_TO_STAGE_INDEX: dict[str, int] = {
    "intent_parser": 0,
    "destination_researcher": 1,
    "lodging": 1,
    "logistics": 1,
    "specialists_parallel": 1,
    "budget": 1,
    "merge": 2,
    "validator": 3,
}

STEP_LABELS: dict[str, str] = {
    "intent_parser": "Intent parser",
    "destination_researcher": "Destination research",
    "lodging": "Lodging",
    "logistics": "Logistics",
    "specialists_parallel": "Specialists (parallel)",
    "budget": "Budget",
    "merge": "Merge itinerary",
    "validator": "Validator",
}


@dataclass
class TraceEntry:
    step: str
    status: str
    ts: str = ""
    duration_ms: Optional[float] = None
    provider: str = ""
    model: str = ""
    error: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TraceEntry":
        return cls(
            step=str(data.get("step", "")),
            status=str(data.get("status", "")),
            ts=str(data.get("ts", "")),
            duration_ms=data.get("duration_ms"),
            provider=str(data.get("provider", "")),
            model=str(data.get("model", "")),
            error=str(data.get("error", "")),
        )


def trace_path_for_run(run_dir: str | Path) -> Path:
    return Path(run_dir) / "trace.jsonl"


def load_trace(run_dir: Optional[str | Path]) -> list[TraceEntry]:
    if not run_dir:
        return []
    path = trace_path_for_run(run_dir)
    if not path.exists():
        return []
    entries: list[TraceEntry] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            entries.append(TraceEntry.from_dict(json.loads(line)))
    except (json.JSONDecodeError, OSError):
        return []
    return entries


def stage_message_from_trace(entries: list[TraceEntry]) -> str:
    if not entries:
        return "Starting pipeline..."
    ok_steps = [e for e in entries if e.status == "ok"]
    if not ok_steps:
        return STAGE_MESSAGES[0]
    last = ok_steps[-1]
    idx = STEP_TO_STAGE_INDEX.get(last.step, 0)
    return STAGE_MESSAGES[min(idx, len(STAGE_MESSAGES) - 1)]


def progress_fraction(entries: list[TraceEntry]) -> float:
    if not entries:
        return 0.05
    ok_steps = [e for e in entries if e.status == "ok"]
    if not ok_steps:
        return 0.05
    max_idx = max(STEP_TO_STAGE_INDEX.get(e.step, 0) for e in ok_steps)
    return min(0.95, (max_idx + 1) / len(STAGE_MESSAGES))


def format_timeline_row(entry: TraceEntry) -> str:
    label = STEP_LABELS.get(entry.step, entry.step.replace("_", " ").title())
    icon = "✅" if entry.status == "ok" else "❌"
    parts = [f"{icon} **{label}**"]
    if entry.duration_ms is not None:
        parts.append(f"({entry.duration_ms:.0f} ms)")
    if entry.provider:
        parts.append(f"· {entry.provider}")
    if entry.ts:
        parts.append(f"· `{entry.ts}`")
    if entry.error:
        parts.append(f"· _{entry.error}_")
    return " ".join(parts)


def render_trace_timeline(entries: list[TraceEntry]) -> None:
    """Render agent timeline (Streamlit markdown). Caller imports streamlit."""
    import streamlit as st

    if not entries:
        st.caption("No trace available yet. Trace appears after a live plan run.")
        return
    for entry in entries:
        st.markdown(format_timeline_row(entry))
