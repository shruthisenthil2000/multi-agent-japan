"""Application configuration and per-agent LLM provider routing."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Literal

from dotenv import load_dotenv

load_dotenv()

Provider = Literal["groq", "gemini"]
DataMode = Literal["llm_only", "mcp_enhanced"]

# Phase 1 two-brain routing (implementation-plan.md)
AGENT_PROVIDERS: dict[str, Provider] = {
    "intent_parser": "groq",
    "destination_researcher": "groq",
    "lodging": "groq",
    "logistics": "groq",
    "merge": "groq",
    "budget": "gemini",
    "validator": "gemini",
}

GROQ_AGENTS = frozenset(k for k, v in AGENT_PROVIDERS.items() if v == "groq")
GEMINI_AGENTS = frozenset(k for k, v in AGENT_PROVIDERS.items() if v == "gemini")


@dataclass(frozen=True)
class Settings:
    data_mode: DataMode = "llm_only"
    groq_api_key: str = ""
    gemini_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    gemini_model: str = "gemini-3-flash"
    rate_limit_enabled: bool = True
    llm_timeout_seconds: float = 120.0
    intent_timeout_seconds: float = 30.0
    specialist_timeout_seconds: float = 120.0
    merge_timeout_seconds: float = 90.0
    validator_timeout_seconds: float = 30.0
    pipeline_timeout_seconds: float = 480.0
    agent_providers: dict[str, Provider] = field(default_factory=lambda: dict(AGENT_PROVIDERS))

    def model_for(self, provider: Provider) -> str:
        if provider == "groq":
            return self.groq_model
        return self.gemini_model

    def provider_for_agent(self, agent_name: str) -> Provider:
        try:
            return self.agent_providers[agent_name]
        except KeyError as e:
            raise KeyError(f"No provider configured for agent: {agent_name}") from e

    def require_api_key(self, provider: Provider) -> None:
        if provider == "groq" and not self.groq_api_key:
            raise ValueError("GROQ_API_KEY is not set")
        if provider == "gemini" and not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not set")


@lru_cache
def get_settings() -> Settings:
    data_mode = os.getenv("DATA_MODE", "llm_only")
    if data_mode not in ("llm_only", "mcp_enhanced"):
        data_mode = "llm_only"
    return Settings(
        data_mode=data_mode,  # type: ignore[arg-type]
        groq_api_key=os.getenv("GROQ_API_KEY", ""),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-3-flash"),
        rate_limit_enabled=os.getenv("RATE_LIMIT_ENABLED", "true").lower()
        in ("1", "true", "yes"),
    )
