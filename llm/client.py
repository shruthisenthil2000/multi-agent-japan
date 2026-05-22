"""LLM clients for Groq and Gemini with complete() and complete_json()."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Callable, Optional, TypeVar

import httpx
from pydantic import BaseModel

from orchestrator.config import Settings, get_settings

T = TypeVar("T", bound=BaseModel)

CompletionFn = Callable[[str, list[dict[str, str]]], str]


class LLMError(Exception):
    pass


class LLMConfigError(LLMError):
    pass


class LLMRateLimitError(LLMError):
    pass


class LLMJSONError(LLMError):
    pass


def _strip_json_fences(text: str) -> str:
    text = text.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        return m.group(1).strip()
    return text


def _parse_json(text: str) -> Any:
    return json.loads(_strip_json_fences(text))


class LLMClient:
    """Provider-specific chat client."""

    def __init__(
        self,
        provider: str,
        *,
        settings: Optional[Settings] = None,
        completion_fn: Optional[CompletionFn] = None,
    ) -> None:
        self.provider = provider
        self.settings = settings or get_settings()
        self._completion_fn = completion_fn
        self.model = self.settings.model_for(provider)

    def complete(self, system: str, user: str) -> str:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        if self._completion_fn is not None:
            return self._completion_fn(self.provider, messages)
        return self._complete_live(messages)

    def complete_json(
        self,
        system: str,
        user: str,
        model_type: type[T],
        *,
        max_retries: int = 1,
    ) -> T:
        json_instruction = (
            "\n\nRespond with valid JSON only, no markdown fences, "
            f"matching this schema: {model_type.model_json_schema()}"
        )
        last_err: Optional[Exception] = None
        for attempt in range(max_retries + 1):
            raw = self.complete(system, user + (json_instruction if attempt == 0 else ""))
            try:
                data = _parse_json(raw)
                return model_type.model_validate(data)
            except (json.JSONDecodeError, ValueError) as e:
                last_err = e
                user = (
                    f"{user}\n\nPrevious response was invalid JSON: {e}. "
                    "Return corrected JSON only."
                )
        raise LLMJSONError(f"Failed to parse JSON after {max_retries + 1} attempts") from last_err

    def _complete_live(self, messages: list[dict[str, str]]) -> str:
        if self.provider == "groq":
            return self._complete_groq(messages)
        if self.provider == "gemini":
            return self._complete_gemini(messages)
        raise LLMConfigError(f"Unknown provider: {self.provider}")

    def _complete_groq(self, messages: list[dict[str, str]]) -> str:
        api_key = self.settings.groq_api_key
        if not api_key:
            raise LLMConfigError("GROQ_API_KEY is not set")
        url = "https://api.groq.com/openai/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.4,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        return self._post_chat(url, headers, payload)

    def _complete_gemini(self, messages: list[dict[str, str]]) -> str:
        api_key = self.settings.gemini_api_key
        if not api_key:
            raise LLMConfigError("GEMINI_API_KEY is not set")
        system = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_parts = [m["content"] for m in messages if m["role"] == "user"]
        user = "\n\n".join(user_parts)
        prompt = f"{system}\n\n{user}" if system else user
        model = self.model
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.4},
        }
        headers = {"Content-Type": "application/json"}
        params = {"key": api_key}
        with httpx.Client(timeout=self.settings.llm_timeout_seconds) as client:
            resp = client.post(url, headers=headers, params=params, json=payload)
            if resp.status_code == 429:
                raise LLMRateLimitError("Gemini rate limit exceeded")
            resp.raise_for_status()
            data = resp.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            raise LLMError(f"Unexpected Gemini response: {data}") from e

    def _post_chat(self, url: str, headers: dict[str, str], payload: dict[str, Any]) -> str:
        with httpx.Client(timeout=self.settings.llm_timeout_seconds) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code == 429:
                raise LLMRateLimitError(f"{self.provider} rate limit exceeded")
            resp.raise_for_status()
            data = resp.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise LLMError(f"Unexpected {self.provider} response: {data}") from e


_clients: dict[str, LLMClient] = {}


def get_client(
    provider: str,
    *,
    settings: Optional[Settings] = None,
    completion_fn: Optional[CompletionFn] = None,
) -> LLMClient:
    """Return a cached or new client for groq | gemini."""
    if provider not in ("groq", "gemini"):
        raise LLMConfigError(f"Unknown provider: {provider}. Use 'groq' or 'gemini'.")
    if completion_fn is not None:
        return LLMClient(provider, settings=settings, completion_fn=completion_fn)
    if provider not in _clients:
        _clients[provider] = LLMClient(provider, settings=settings)
    return _clients[provider]


def clear_client_cache() -> None:
    _clients.clear()
