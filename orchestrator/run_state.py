"""Persist pipeline artifacts and trace per run."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Optional


class RunState:
    ARTIFACTS = {
        "request": "00_request.txt",
        "travel_brief": "01_travel_brief.json",
        "research": "02_research.json",
        "lodging": "03_lodging.json",
        "logistics": "04_logistics.json",
        "budget": "05_budget.json",
        "draft": "06_draft_itinerary.md",
        "validation": "07_validation.json",
        "final": "08_final_itinerary.md",
    }

    def __init__(self, run_id: Optional[str] = None, base_dir: Optional[Path] = None) -> None:
        self.run_id = run_id or uuid.uuid4().hex[:12]
        self.base_dir = base_dir or Path("runs")
        self.dir = self.base_dir / self.run_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self._trace_path = self.dir / "trace.jsonl"

    def write_text(self, key: str, content: str) -> Path:
        filename = self.ARTIFACTS.get(key, key)
        path = self.dir / filename
        path.write_text(content, encoding="utf-8")
        return path

    def write_json(self, key: str, data: Any) -> Path:
        return self.write_text(key, json.dumps(data, indent=2, ensure_ascii=False))

    def trace(
        self,
        step: str,
        *,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        duration_ms: Optional[float] = None,
        status: str = "ok",
        error: Optional[str] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> None:
        entry: dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "step": step,
            "status": status,
        }
        if provider:
            entry["provider"] = provider
        if model:
            entry["model"] = model
        if duration_ms is not None:
            entry["duration_ms"] = round(duration_ms, 1)
        if error:
            entry["error"] = error
        if extra:
            entry.update(extra)
        with self._trace_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
