"""Offline demo itinerary from committed canonical example — no API calls."""

from __future__ import annotations

import json
from pathlib import Path

from orchestrator.pipeline import PlanTripResult

_REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_DIR = _REPO_ROOT / "examples" / "canonical-japan"
DEMO_RUN_ID = "canonical-japan-demo"


def canonical_example_available() -> bool:
    return (CANONICAL_DIR / "08_final_itinerary.md").exists()


def load_demo_result() -> PlanTripResult:
    """Build PlanTripResult from examples/canonical-japan without invoking the pipeline."""
    if not canonical_example_available():
        raise FileNotFoundError(
            f"Canonical demo data missing at {CANONICAL_DIR}. "
            "Ensure examples/canonical-japan is present in the repo."
        )

    final_path = CANONICAL_DIR / "08_final_itinerary.md"
    validation_status = "pass"
    val_path = CANONICAL_DIR / "07_validation.json"
    if val_path.exists():
        try:
            data = json.loads(val_path.read_text(encoding="utf-8"))
            validation_status = str(data.get("status", data.get("overall_status", "pass")))
        except (json.JSONDecodeError, OSError):
            pass

    artifacts = {
        key: str(CANONICAL_DIR / name)
        for key, name in (
            ("request", "00_request.txt"),
            ("travel_brief", "01_travel_brief.json"),
            ("research", "02_research.json"),
            ("lodging", "03_lodging.json"),
            ("logistics", "04_logistics.json"),
            ("budget", "05_budget.json"),
            ("draft", "06_draft_itinerary.md"),
            ("validation", "07_validation.json"),
            ("final", "08_final_itinerary.md"),
        )
        if (CANONICAL_DIR / name).exists()
    }

    return PlanTripResult(
        run_id=DEMO_RUN_ID,
        run_dir=str(CANONICAL_DIR.resolve()),
        final_markdown=final_path.read_text(encoding="utf-8"),
        validation_status=validation_status,
        artifacts=artifacts,
    )


def demo_request_text() -> str:
    req = CANONICAL_DIR / "00_request.txt"
    if req.exists():
        return req.read_text(encoding="utf-8").strip()
    return (
        "Plan a 5-day trip to Japan. Tokyo + Kyoto. $3,000 budget. "
        "Love food and temples, hate crowds."
    )
