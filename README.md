# Multi Agent_Tokyo

Travel Planning Multi-Agent System — turns a natural-language trip request into a structured itinerary.

**Current status:** Phase 0 (foundation). Phase 1 adds the full LLM pipeline.

## Setup

Requires **Python 3.9+**.

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env          # add GROQ_API_KEY and GEMINI_API_KEY
```

## Two-brain LLM routing (Phase 1+)

| Provider | Agents |
|----------|--------|
| **Groq** | `intent_parser`, `destination_researcher`, `lodging`, `logistics`, `merge` |
| **Gemini** | `budget`, `validator` |

## Rate limits (account tier)

| Provider | Model | RPM | TPM | RPD |
|----------|-------|-----|-----|-----|
| Groq | `llama-3.3-70b-versatile` | 30 | 12K | 1K (also 100K TPD) |
| Gemini | `gemini-3-flash` | **5** | 250K | **20** |

Phase 1 runs Gemini **sequentially** with spacing (~12s). Expect **~10 full demo runs/day** on Gemini. Details: [implementation-plan.md](docs/implementation-plan.md#provider-rate-limits-account-quota).

## Run (Phase 1 — live LLM)

```bash
# Requires GROQ_API_KEY and GEMINI_API_KEY in .env
python -m orchestrator.cli "Plan a 5-day trip to Japan. Tokyo + Kyoto. \$3,000 budget. Love food and temples, hate crowds."
# or: plan-trip "..."
```

Artifacts are written under `runs/<run_id>/` (`00_request.txt` … `08_final_itinerary.md`).

## Tests

```bash
pytest
```

## Docs

- [problemstatement.md](docs/problemstatement.md)
- [architecture.md](docs/architecture.md)
- [implementation-plan.md](docs/implementation-plan.md)
