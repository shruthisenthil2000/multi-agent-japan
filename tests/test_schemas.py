import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from llm.schemas import (
    BudgetPlan,
    LogisticsPlan,
    ResearchPack,
    TravelBrief,
    ValidationReport,
)

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


class TestTravelBrief:
    def test_valid_fixture_round_trip(self):
        data = load_fixture("travel_brief_valid.json")
        brief = TravelBrief.model_validate(data)
        assert brief.duration_days == 5
        assert brief.destinations[0].city == "Tokyo"
        assert brief.destinations[1].days == 2
        dumped = brief.model_dump(mode="json")
        assert TravelBrief.model_validate(dumped).duration_days == 5

    def test_extra_fields_ignored(self):
        data = load_fixture("travel_brief_extra_fields.json")
        brief = TravelBrief.model_validate(data)
        assert not hasattr(brief, "unexpected_llm_field")

    def test_architecture_example(self):
        data = load_fixture("travel_brief_canonical.json")
        brief = TravelBrief.model_validate(data)
        assert brief.budget.amount == 3000


class TestResearchPack:
    def test_invalid_enum_rejected(self):
        data = load_fixture("research_pack_invalid_enum.json")
        with pytest.raises(ValidationError):
            ResearchPack.model_validate(data)

    def test_architecture_example(self):
        data = {
            "schema_version": "1.0",
            "cities": {
                "Tokyo": {
                    "activities": [
                        {
                            "name": "Senso-ji",
                            "type": "temple",
                            "crowd_level": "high",
                            "suggested_timing": "early_morning",
                            "why": "Iconic temple; quieter before 8am",
                        }
                    ],
                    "food_areas": ["Tsukiji Outer", "Shimokitazawa"],
                },
                "Kyoto": {"activities": [], "food_areas": []},
            },
            "sources": [],
        }
        pack = ResearchPack.model_validate(data)
        assert pack.cities["Tokyo"].activities[0].name == "Senso-ji"


class TestLogisticsPlan:
    def test_architecture_example(self):
        data = {
            "schema_version": "1.0",
            "transfers": [
                {
                    "from": "Tokyo",
                    "to": "Kyoto",
                    "day": 3,
                    "mode": "Shinkansen",
                    "duration_minutes": 150,
                    "cost_estimate_usd": {"low": 100, "high": 140},
                    "notes": "Reserve seats",
                }
            ],
            "sources": [],
        }
        plan = LogisticsPlan.model_validate(data)
        assert plan.transfers[0].from_city == "Tokyo"


class TestBudgetPlan:
    def test_architecture_example(self):
        data = {
            "schema_version": "1.0",
            "total": {"amount": 3000, "currency": "USD"},
            "categories": [
                {"name": "lodging", "amount": 900, "percent": 30},
                {"name": "food", "amount": 750, "percent": 25},
                {"name": "local_transport", "amount": 300, "percent": 10},
                {"name": "intercity", "amount": 250, "percent": 8},
                {"name": "activities", "amount": 500, "percent": 17},
                {"name": "buffer", "amount": 300, "percent": 10},
            ],
            "tradeoffs": ["If lodging exceeds $900, reduce paid experiences"],
        }
        plan = BudgetPlan.model_validate(data)
        assert sum(c.amount for c in plan.categories) == 3000

    def test_category_sum_validation(self):
        data = {
            "schema_version": "1.0",
            "total": {"amount": 3000, "currency": "USD"},
            "categories": [
                {"name": "lodging", "amount": 500, "percent": 20},
                {"name": "food", "amount": 500, "percent": 20},
            ],
            "tradeoffs": [],
        }
        with pytest.raises(ValidationError):
            BudgetPlan.model_validate(data)


class TestValidationReport:
    def test_architecture_example(self):
        data = {
            "schema_version": "1.0",
            "status": "pass_with_gaps",
            "checks": [
                {"id": "duration", "ok": True},
                {"id": "budget_discussed", "ok": True},
            ],
            "gaps": [
                {"severity": "low", "message": "No explicit temple day in Kyoto labeled"}
            ],
        }
        report = ValidationReport.model_validate(data)
        assert report.status == "pass_with_gaps"
