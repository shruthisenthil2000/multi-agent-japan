"""Agent protocol and shared context/result types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Protocol, runtime_checkable

from pydantic import BaseModel

from orchestrator.config import Provider, get_settings


@dataclass
class AgentContext:
    run_id: str
    travel_brief: Optional[dict[str, Any]] = None
    artifacts: dict[str, Any] = field(default_factory=dict)
    tools_enabled: bool = False

    def get_artifact(self, key: str) -> Optional[Any]:
        return self.artifacts.get(key)


@dataclass
class AgentResult:
    payload: dict[str, Any]
    summary: str = ""
    sources: list[dict[str, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    provider: Optional[Provider] = None
    model: Optional[str] = None

    def to_json_dict(self) -> dict[str, Any]:
        return self.payload


@runtime_checkable
class Agent(Protocol):
    name: str

    @property
    def provider(self) -> Provider:
        ...

    def run(self, ctx: AgentContext) -> AgentResult:
        ...


class BaseAgent:
    """Optional convenience base for Phase 1 agent implementations."""

    name: str = "base"

    @property
    def provider(self) -> Provider:
        return get_settings().provider_for_agent(self.name)

    def run(self, ctx: AgentContext) -> AgentResult:
        raise NotImplementedError


def pack_model(model: BaseModel, *, provider: Optional[Provider] = None) -> AgentResult:
    settings = get_settings()
    prov = provider or settings.provider_for_agent(getattr(model, "_agent_name", "unknown"))
    return AgentResult(
        payload=model.model_dump(mode="json", by_alias=True),
        provider=prov if provider else None,
        model=settings.model_for(prov) if provider else None,
    )
