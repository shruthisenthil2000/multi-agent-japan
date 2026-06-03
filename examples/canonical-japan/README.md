# Canonical Japan golden run (Phase 2)

Committed output from a **live Phase 1** pipeline run (LLM-only, no MCP).

| Field | Value |
|-------|--------|
| **Source run** | `596da9cd4964` |
| **Request** | Plan a 5-day trip to Japan. Tokyo + Kyoto. $3,000 budget. Love food and temples, hate crowds. |
| **Validation** | `pass` |
| **Providers** | Groq (`llama-3.3-70b-versatile`) + Gemini (`gemini-3-flash`) |

## Files

| File | Agent / step |
|------|----------------|
| `00_request.txt` | User input |
| `01_travel_brief.json` | Intent parser (Groq) |
| `02_research.json` | Destination researcher (Groq) |
| `03_lodging.json` | Lodging (Groq) |
| `04_logistics.json` | Logistics (Groq) |
| `05_budget.json` | Budget (Gemini) |
| `06_draft_itinerary.md` | Merge (Groq) |
| `07_validation.json` | Validator (Gemini) |
| `08_final_itinerary.md` | Final deliverable |
| `trace.jsonl` | Step timings and providers |

## Regenerate (uses API quota)

```bash
python -m orchestrator.cli "Plan a 5-day trip to Japan. Tokyo + Kyoto. \$3,000 budget. Love food and temples, hate crowds."
cp runs/<new_run_id>/* examples/canonical-japan/
```

Do not run full `pytest` before demos if Gemini **RPD (20/day)** is tight — use `pytest tests/test_acceptance.py` (reads this folder only).
