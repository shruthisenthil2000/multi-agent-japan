"""Thin API wrapper for UI and external callers."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from orchestrator.pipeline import PlanTripResult, plan_trip_sync


def run_trip(
    request: str,
    *,
    run_id: Optional[str] = None,
    runs_base_dir: Optional[Path] = None,
) -> PlanTripResult:
    """Run the existing multi-agent pipeline without modifying orchestration."""
    return plan_trip_sync(
        request,
        run_id=run_id,
        runs_base_dir=runs_base_dir,
    )


__all__ = ["run_trip", "PlanTripResult"]
