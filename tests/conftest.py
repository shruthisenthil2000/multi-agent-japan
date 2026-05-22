import json
from pathlib import Path

import pytest

from llm.client import clear_client_cache
from orchestrator.config import get_settings

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


@pytest.fixture(autouse=True)
def _reset_clients():
    clear_client_cache()
    get_settings.cache_clear()
    yield
    clear_client_cache()
    get_settings.cache_clear()


@pytest.fixture
def mock_completion_fn():
    """Route mock LLM responses by agent role in system prompt."""

    def _fn(provider: str, messages: list) -> str:
        system = messages[0]["content"] if messages else ""
        if "Intent Parser" in system:
            return _load("travel_brief_valid.json")
        if "Destination Researcher" in system:
            return _load("research_pack_canonical.json")
        if "Lodging" in system:
            return _load("lodging_plan_canonical.json")
        if "Logistics agent" in system:
            return _load("logistics_plan_canonical.json")
        if "Budget agent" in system:
            return _load("budget_plan_canonical.json")
        if "Validator" in system:
            return _load("validation_pass.json")
        if "Merge" in system or "Coordinator" in system:
            return _load("draft_itinerary_canonical.md")
        return "{}"

    return _fn


@pytest.fixture
def canonical_request():
    return (
        "Plan a 5-day trip to Japan. Tokyo + Kyoto. $3,000 budget. "
        "Love food and temples, hate crowds."
    )
