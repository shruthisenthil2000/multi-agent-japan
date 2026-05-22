"""
Token-bucket style spacing for provider RPM limits (Phase 1+).

Usage in pipeline:
    limiter = ProviderRateLimiter.from_settings()
    await limiter.acquire("groq")
    client.complete(...)
"""

from __future__ import annotations

import asyncio
import json
import time
from datetime import date
from pathlib import Path
from typing import Literal, Optional, Union

from orchestrator.rate_limits import Provider, get_rate_limits

ProviderName = Literal["groq", "gemini"]

_DEFAULT_USAGE_DIR = Path("runs/.quota")


class RateLimitExceeded(Exception):
    """Daily request quota exhausted for a provider."""

    def __init__(self, provider: str, used: int, limit: int) -> None:
        super().__init__(
            f"{provider} daily request limit reached ({used}/{limit}). "
            "Try again tomorrow or raise GEMINI_RPD / GROQ_RPD."
        )
        self.provider = provider
        self.used = used
        self.limit = limit


class ProviderRateLimiter:
    """Enforces RPM spacing and optional RPD counters on disk."""

    def __init__(
        self,
        usage_dir: Optional[Path] = None,
        groq_model: Optional[str] = None,
        gemini_model: Optional[str] = None,
    ) -> None:
        self._usage_dir = usage_dir or _DEFAULT_USAGE_DIR
        self._last_request: dict[str, float] = {}
        self._groq_model = groq_model
        self._gemini_model = gemini_model
        self._lock: Optional[asyncio.Lock] = None

    @classmethod
    def from_settings(cls) -> ProviderRateLimiter:
        from orchestrator.config import get_settings

        s = get_settings()
        return cls(groq_model=s.groq_model, gemini_model=s.gemini_model)

    def _limits(self, provider: ProviderName):
        model = self._groq_model if provider == "groq" else self._gemini_model
        return get_rate_limits(provider, model)

    def _usage_file(self, provider: ProviderName) -> Path:
        self._usage_dir.mkdir(parents=True, exist_ok=True)
        return self._usage_dir / f"{provider}_{date.today().isoformat()}.json"

    def _read_daily_count(self, provider: ProviderName) -> int:
        path = self._usage_file(provider)
        if not path.exists():
            return 0
        try:
            data = json.loads(path.read_text())
            return int(data.get("requests", 0))
        except (json.JSONDecodeError, TypeError, ValueError):
            return 0

    def _increment_daily(self, provider: ProviderName) -> int:
        path = self._usage_file(provider)
        count = self._read_daily_count(provider) + 1
        path.write_text(json.dumps({"requests": count, "date": date.today().isoformat()}))
        return count

    def check_daily_quota(self, provider: ProviderName) -> None:
        limits = self._limits(provider)
        used = self._read_daily_count(provider)
        if used >= limits.requests_per_day:
            raise RateLimitExceeded(provider, used, limits.requests_per_day)

    def acquire_sync(self, provider: ProviderName) -> None:
        """Block until RPM spacing allows another request; bump RPD counter."""
        self.check_daily_quota(provider)
        limits = self._limits(provider)
        min_gap = limits.min_seconds_between_requests
        now = time.monotonic()
        last = self._last_request.get(provider, 0.0)
        wait = min_gap - (now - last)
        if wait > 0:
            time.sleep(wait)
        self._last_request[provider] = time.monotonic()
        self._increment_daily(provider)

    async def acquire(self, provider: ProviderName) -> None:
        if self._lock is None:
            self._lock = asyncio.Lock()
        async with self._lock:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.acquire_sync, provider)
