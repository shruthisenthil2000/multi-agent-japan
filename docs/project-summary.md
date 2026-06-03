# Project Summary

**Voice-Enabled Multi-Agent Travel Planner** — recruiter and interview overview.

---

## Problem

Planning a multi-city trip requires balancing destinations, budget, lodging, logistics, and daily activities. Single-shot LLM prompts often miss structure, validation, or consistent budgets. Users also want a conversational entry point (voice or text) before committing API cost.

---

## Solution

A **coordinator-led multi-agent pipeline** turns one natural-language request into a validated markdown itinerary with JSON artifacts. A **Streamlit voice copilot** collects required slots (destination, duration, budget) before calling the pipeline, shows live progress from `trace.jsonl`, and supports **offline demo mode** for presentations without API keys.

---

## Architecture

```text
User → Streamlit UI → Conversation (slots) → run_trip()
     → plan_trip_sync() → Groq specialists (parallel) → Gemini budget/validator
     → merge → artifacts → rich itinerary UI
```

- **UI layer** (`app/`) is additive; pipeline unchanged.
- **No** LangGraph or separate workflow engine.
- Entry points: `streamlit run app/voice_agent.py`, `plan-trip` CLI, `orchestrator.api.run_trip`.

Full diagram: [assets/architecture-diagram.md](assets/architecture-diagram.md).

---

## Tech stack

| Layer | Technologies |
|-------|----------------|
| LLM routing | Groq (`llama-3.3-70b-versatile`), Gemini (`gemini-3-flash`) |
| Orchestration | `asyncio` pipeline, `RunState` artifacts |
| Contracts | Pydantic schemas (`llm/schemas.py`) |
| UI | Streamlit, optional `speechrecognition` + `pyttsx3` |
| Export | Markdown, ReportLab PDF |
| Config | `python-dotenv`, rate limiter |
| Tests | pytest, mock LLM fixtures |

---

## Key engineering decisions

1. **Two-brain routing** — Fast Groq for breadth; Gemini for budget + validation under stricter quota.
2. **Slot gating in UI** — Pipeline runs only when required fields are present (saves quota, better prompts).
3. **Trace-driven progress** — UI polls `trace.jsonl` during runs without modifying pipeline code.
4. **Demo mode** — Canonical `examples/canonical-japan/` for zero-API portfolio demos.
5. **LLM-only Phase 1** — Live booking/maps data deferred to Phase L+ (MCP/KB).

---

## Tradeoffs

| Choice | Benefit | Cost |
|--------|---------|------|
| Rule-based slot filling | No extra LLM calls in chat | Complex phrasing needs multiple turns |
| Streamlit | Fast portfolio UI | Not ideal for multi-tenant production |
| LLM-generated data | Rapid MVP | Not verified against live prices/availability |
| Gemini free tier | Low cost | ~10 full plans/day |

---

## Future roadmap

- **L+** — Bright Data MCP, neighborhood KB, live transport/lodging signals.
- **Optional LLM slots** — Small extraction call in UI only.
- **FastAPI wrapper** — Same `run_trip()` for mobile or team backends.
- **Stronger evals** — Golden runs + automated regression on artifacts.

---

## Quick facts for interviews

- **~6 Groq + ~2 Gemini calls** per full plan.
- **Artifacts:** `00_request.txt` … `08_final_itinerary.md`, `trace.jsonl`.
- **Tests:** Mock pipeline + voice/portfolio suites (no API in CI).
- **Demo:** Sidebar → Demo mode → Use demo itinerary.

---

## Links

- [README](../README.md) — install & quickstart
- [demo-script.md](demo-script.md) — 5-minute walkthrough
- [deployment.md](deployment.md) — Docker & Streamlit Cloud
