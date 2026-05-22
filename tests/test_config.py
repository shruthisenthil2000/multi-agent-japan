from orchestrator.config import AGENT_PROVIDERS, GEMINI_AGENTS, GROQ_AGENTS


def test_agent_providers_two_brain_routing():
    assert AGENT_PROVIDERS["destination_researcher"] == "groq"
    assert AGENT_PROVIDERS["lodging"] == "groq"
    assert AGENT_PROVIDERS["logistics"] == "groq"
    assert AGENT_PROVIDERS["budget"] == "gemini"
    assert AGENT_PROVIDERS["validator"] == "gemini"
    assert AGENT_PROVIDERS["intent_parser"] == "groq"
    assert AGENT_PROVIDERS["merge"] == "groq"


def test_groq_gemini_agent_sets():
    assert "budget" in GEMINI_AGENTS
    assert "validator" in GEMINI_AGENTS
    assert "destination_researcher" in GROQ_AGENTS
    assert "budget" not in GROQ_AGENTS
