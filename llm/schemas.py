"""Pydantic data contracts for inter-agent JSON handoffs (schema_version 1.0)."""

from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SCHEMA_VERSION = "1.0"


class StrictModel(BaseModel):
    """Base model: ignore unknown fields from LLM output (EVAL-SCH-003)."""

    model_config = ConfigDict(extra="ignore")


# --- Shared enums ---


class Pace(str, Enum):
    relaxed = "relaxed"
    moderate = "moderate"
    fast = "fast"


class BudgetFlexibility(str, Enum):
    strict = "strict"
    flexible = "flexible"


class CrowdLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class SuggestedTiming(str, Enum):
    early_morning = "early_morning"
    morning = "morning"
    afternoon = "afternoon"
    evening = "evening"
    off_peak = "off_peak"


class DataConfidence(str, Enum):
    verified = "verified"
    typical = "typical"
    inferred = "inferred"


class ValidationStatus(str, Enum):
    pass_ = "pass"
    pass_with_gaps = "pass_with_gaps"
    fail = "fail"

    @classmethod
    def values(cls) -> set[str]:
        return {"pass", "pass_with_gaps", "fail"}


class GapSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


# --- TravelBrief ---


class Money(StrictModel):
    amount: float = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    flexibility: Optional[BudgetFlexibility] = None


class Destination(StrictModel):
    city: str
    country: str
    days: int = Field(ge=1)


class TravelBrief(StrictModel):
    schema_version: Literal["1.0"] = SCHEMA_VERSION
    duration_days: int = Field(ge=1)
    destinations: list[Destination] = Field(min_length=1)
    budget: Money
    preferences: list[str] = Field(default_factory=list)
    anti_preferences: list[str] = Field(default_factory=list)
    pace: Pace = Pace.moderate
    party_size: int = Field(default=2, ge=1)
    notes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def days_align_with_duration(self) -> TravelBrief:
        total = sum(d.days for d in self.destinations)
        if total != self.duration_days:
            self.warnings = [
                *self.warnings,
                f"Destination days ({total}) differ from duration_days ({self.duration_days}).",
            ]
        return self


# --- ResearchPack ---


class Source(StrictModel):
    url: str
    title: str = ""
    fetched_at: Optional[str] = None


class Activity(StrictModel):
    name: str
    type: str
    crowd_level: CrowdLevel
    suggested_timing: SuggestedTiming
    why: str
    data_confidence: DataConfidence = DataConfidence.inferred


class CityResearch(StrictModel):
    activities: list[Activity] = Field(default_factory=list)
    food_areas: list[str] = Field(default_factory=list)


class ResearchPack(StrictModel):
    schema_version: Literal["1.0"] = SCHEMA_VERSION
    cities: dict[str, CityResearch]
    sources: list[Source] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    data_confidence: DataConfidence = DataConfidence.inferred


# --- LodgingPlan ---


class Neighborhood(StrictModel):
    neighborhood: str
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    fit_score: float = Field(ge=0.0, le=1.0)
    data_confidence: DataConfidence = DataConfidence.inferred


class LodgingPlan(StrictModel):
    schema_version: Literal["1.0"] = SCHEMA_VERSION
    cities: dict[str, list[Neighborhood]]
    warnings: list[str] = Field(default_factory=list)
    data_confidence: DataConfidence = DataConfidence.inferred


# --- LogisticsPlan ---


class CostBand(StrictModel):
    low: float = Field(ge=0)
    high: float = Field(ge=0)

    @model_validator(mode="after")
    def low_lte_high(self) -> CostBand:
        if self.low > self.high:
            raise ValueError("cost low must be <= high")
        return self


class Transfer(StrictModel):
    from_city: str = Field(alias="from")
    to_city: str = Field(alias="to")
    day: int = Field(ge=1)
    mode: str
    duration_minutes: int = Field(ge=1)
    cost_estimate_usd: Optional[CostBand] = None
    notes: str = ""
    data_confidence: DataConfidence = DataConfidence.typical

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class LogisticsPlan(StrictModel):
    schema_version: Literal["1.0"] = SCHEMA_VERSION
    transfers: list[Transfer] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    data_confidence: DataConfidence = DataConfidence.inferred


# --- BudgetPlan ---


class BudgetCategory(StrictModel):
    name: str
    amount: float = Field(ge=0)
    percent: float = Field(ge=0, le=100)


class BudgetPlan(StrictModel):
    schema_version: Literal["1.0"] = SCHEMA_VERSION
    total: Money
    categories: list[BudgetCategory] = Field(min_length=1)
    tradeoffs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    data_confidence: DataConfidence = DataConfidence.typical

    @model_validator(mode="after")
    def categories_sum_near_total(self) -> BudgetPlan:
        cat_sum = sum(c.amount for c in self.categories)
        tolerance = self.total.amount * 0.02
        if abs(cat_sum - self.total.amount) > tolerance:
            raise ValueError(
                f"Category sum {cat_sum} must be within 2% of total {self.total.amount}"
            )
        return self


# --- ValidationReport ---


class ValidationCheck(StrictModel):
    id: str
    ok: bool
    note: str = ""


class ValidationGap(StrictModel):
    severity: GapSeverity
    message: str


class ValidationReport(StrictModel):
    schema_version: Literal["1.0"] = SCHEMA_VERSION
    status: Literal["pass", "pass_with_gaps", "fail"]
    checks: list[ValidationCheck] = Field(default_factory=list)
    gaps: list[ValidationGap] = Field(default_factory=list)

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: str) -> str:
        if v not in ValidationStatus.values():
            raise ValueError(f"Invalid status: {v}")
        return v


# --- Provenance helper (Phase 1) ---

LLM_ONLY_WARNING = "Plan based on model knowledge; not verified against live sources."


def with_llm_provenance(model: StrictModel) -> StrictModel:
    """Attach Phase 1 disclaimer to packs that support warnings/data_confidence."""
    if hasattr(model, "warnings"):
        w = list(model.warnings)  # type: ignore[attr-defined]
        if LLM_ONLY_WARNING not in w:
            w.append(LLM_ONLY_WARNING)
            object.__setattr__(model, "warnings", w)
    if hasattr(model, "data_confidence"):
        object.__setattr__(model, "data_confidence", DataConfidence.inferred)
    if hasattr(model, "sources") and not model.sources:  # type: ignore[attr-defined]
        pass  # keep empty
    return model
