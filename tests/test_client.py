import json

import pytest

from llm.client import LLMClient, LLMConfigError, LLMJSONError, clear_client_cache, get_client
from llm.schemas import TravelBrief
from orchestrator.config import Settings


@pytest.fixture(autouse=True)
def _clear_clients():
    clear_client_cache()
    yield
    clear_client_cache()


def _brief_json() -> str:
    return json.dumps(
        {
            "schema_version": "1.0",
            "duration_days": 5,
            "destinations": [
                {"city": "Tokyo", "country": "Japan", "days": 3},
                {"city": "Kyoto", "country": "Japan", "days": 2},
            ],
            "budget": {"amount": 3000, "currency": "USD"},
            "preferences": ["food", "temples"],
            "anti_preferences": ["crowds"],
            "pace": "moderate",
            "party_size": 2,
            "notes": [],
            "warnings": [],
        }
    )


def test_complete_json_groq_mock():
    calls: list[str] = []

    def fake(_provider: str, _messages: list[dict[str, str]]) -> str:
        calls.append("ok")
        if len(calls) == 1:
            return "not json"
        return _brief_json()

    settings = Settings(groq_api_key="test", gemini_api_key="test")
    client = LLMClient("groq", settings=settings, completion_fn=fake)
    brief = client.complete_json("system", "user", TravelBrief, max_retries=1)
    assert brief.duration_days == 5
    assert len(calls) == 2


def test_complete_json_gemini_mock():
    def fake(_provider: str, _messages: list[dict[str, str]]) -> str:
        return _brief_json()

    settings = Settings(groq_api_key="test", gemini_api_key="test")
    client = LLMClient("gemini", settings=settings, completion_fn=fake)
    brief = client.complete_json("system", "user", TravelBrief)
    assert brief.destinations[1].city == "Kyoto"


def test_complete_json_fails_after_retries():
    def fake(_provider: str, _messages: list[dict[str, str]]) -> str:
        return "still not json"

    settings = Settings(groq_api_key="test", gemini_api_key="test")
    client = LLMClient("groq", settings=settings, completion_fn=fake)
    with pytest.raises(LLMJSONError):
        client.complete_json("s", "u", TravelBrief, max_retries=1)


def test_missing_groq_key_live():
    settings = Settings(groq_api_key="", gemini_api_key="x")
    client = LLMClient("groq", settings=settings)
    with pytest.raises(LLMConfigError, match="GROQ_API_KEY"):
        client.complete("s", "u")


def test_missing_gemini_key_live():
    settings = Settings(groq_api_key="x", gemini_api_key="")
    client = LLMClient("gemini", settings=settings)
    with pytest.raises(LLMConfigError, match="GEMINI_API_KEY"):
        client.complete("s", "u")


def test_get_client_unknown_provider():
    with pytest.raises(LLMConfigError):
        get_client("openai")
