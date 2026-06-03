# Voice AI Travel Agent

Additive Streamlit UI over the existing **Multi Agent_Tokyo** pipeline. The multi-agent orchestrator is unchanged; the voice layer only calls `plan_trip_sync` via `orchestrator.api.run_trip`.

---

## Architecture overview

```text
┌─────────────────────────────────────────────────────────────┐
│  app/voice_agent.py (Streamlit)                               │
│    ├── conversation.py   slot filling + composed_request    │
│    ├── speech.py         STT / TTS (optional)               │
│    ├── itinerary_parser.py  cards from MD + JSON artifacts    │
│    └── export.py         Markdown / PDF download            │
└───────────────────────────┬─────────────────────────────────┘
                            │ run_trip(request)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  orchestrator/api.py  →  orchestrator/pipeline.py           │
│    plan_trip_sync → intent → specialists → merge → validate │
└─────────────────────────────────────────────────────────────┘
```

**Not used (do not add without design):** `workflows/`, LangGraph, `graph.invoke()`, `planner.run()`.

---

## Discovered execution flow

| Step | Component | Provider |
|------|-----------|----------|
| Entry | `orchestrator.api.run_trip` → `plan_trip_sync` | — |
| 1 | `IntentParserAgent` | Groq |
| 2 | `DestinationResearcher`, `Lodging`, `Logistics` (parallel) | Groq |
| 3 | `BudgetAgent` | Gemini |
| 4 | `merge_itinerary` | Groq |
| 5 | `ValidatorAgent` (+ optional retry) | Gemini |

Artifacts: `runs/<run_id>/00_request.txt` … `08_final_itinerary.md`, `trace.jsonl`.

---

## Conversation flow

1. User speaks or types in the left panel.
2. `ConversationManager` extracts slots (rule-based MVP):
   - **Required:** destinations, duration, budget
   - **Optional:** travel style, companions, preferences
3. Assistant asks clarification questions until **required** slots are filled:
   - destinations, duration, budget (in that priority order)
   - Optional: travel style, companions, preferences (prompted after required slots are complete)
4. User clicks **Generate trip** → `build_composed_request()` → one NL string.
5. `run_trip(composed)` runs the full pipeline (~30–60s).
6. Right panel renders parsed itinerary; export/regenerate available.

The pipeline is **not** called on every chat turn — only after explicit generate (or regenerate).

---

## Voice pipeline

| Feature | Library | Notes |
|---------|---------|-------|
| Speech-to-text | `speechrecognition` + Google Web API | Needs network; Mac mic permission |
| Text-to-speech | `pyttsx3` | Optional toggle; runs in background thread |

Install optional stack:

```bash
pip install -e ".[voice]"
```

If voice packages are missing, the app works fully via text input.

### Mac microphone permissions

System Settings → Privacy & Security → Microphone → enable Terminal or your IDE.

### Common STT issues

| Issue | Mitigation |
|-------|------------|
| Timeout | Speak after clicking Speak; check mic input device |
| Permission denied | Grant mic access; restart terminal |
| API failure | Check internet (Google SR) |
| Empty transcript | Retry in a quieter environment |

---

## UI architecture

- **Left:** Onboarding, slot checklist (✅/❌), chat, Speak / Send / Clear, Generate trip.
- **Right:** Rich itinerary (collapsible days, budget/logistics/stay sidebars), exports, agent timeline.
- **Sidebar:** Environment status, demo mode, load demo itinerary.

### Demo mode

Sidebar → **Demo mode** → **Use demo itinerary** loads `examples/canonical-japan/` with **no** `plan_trip_sync` or API calls.

### Planning progress

During live generate, the UI polls `runs/<run_id>/trace.jsonl` and shows:

1. Parsing request…
2. Running specialists…
3. Merging itinerary…
4. Validating plan…

Session state survives Streamlit reruns (`st.session_state`).

---

## Installation

From repository root (Python **3.9+**):

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[voice]"   # core + Streamlit + speech + PDF
cp .env.example .env        # GROQ_API_KEY, GEMINI_API_KEY for live plans
```

---

## Running locally

```bash
streamlit run app/voice_agent.py
```

**Demo (no keys):** sidebar → **Demo mode** → **Use demo itinerary**.

CLI planner (unchanged):

```bash
plan-trip "Plan a 5-day trip to Japan. Tokyo + Kyoto. $3,000 budget."
```

---

## Streamlit + asyncio notes

- `plan_trip_sync` internally uses `asyncio.run(plan_trip(...))`.
- The UI calls `run_trip` inside `st.spinner` on the main Streamlit thread (blocking). This is acceptable for MVP.
- Do not nest `asyncio.run` inside an already-running event loop without `asyncio.run` in a thread.

---

## Quota considerations

| Provider | Typical use per full plan |
|----------|---------------------------|
| Groq | ~6 calls |
| Gemini | ~2 calls (budget + validator) |

Gemini free tier **RPD ≈ 20** → ~10 full plans/day. Regenerate burns more quota.

Set `RATE_LIMIT_ENABLED=true` in `.env` (default).

---

## Verification (Phase 3)

Run voice-layer tests without API keys:

```bash
python3 -m pytest tests/test_voice_app.py -q
```

Streamlit smoke test (from repo root):

```bash
streamlit run app/voice_agent.py
```

## Known limitations

- Conversation slot filling is **rule-based**, not LLM — complex phrasing may need multiple turns.
- Budget phrases like `under 3000` (no `$`) are supported; malformed amounts (`$$$`) are ignored.
- Itinerary day cards use **Morning/Afternoon/Evening** from `02_research.json` when present; otherwise markdown day bullets are used.
- No streaming tokens from agents during planning (spinner only).
- Google STT sends audio to Google’s service (privacy/network).
- PDF export is plain text layout via ReportLab (not styled like a travel brochure).
- No live Places/Booking/Directions APIs (Phase L+ in implementation plan).

---

## Files

| Path | Role |
|------|------|
| `app/voice_agent.py` | Streamlit main |
| `app/conversation.py` | Slots + composed request |
| `app/speech.py` | STT/TTS |
| `app/itinerary_parser.py` | UI model from MD/JSON |
| `app/export.py` | Downloads |
| `orchestrator/api.py` | Thin `run_trip` wrapper |
| `app/progress.py` | Trace.jsonl timeline |
| `app/demo_data.py` | Offline canonical demo |
| `app/env_check.py` | Startup env validation |
| `app/itinerary_ui.py` | Rich Streamlit rendering |
| `tests/test_voice_app.py` | Voice-layer unit tests (no live API) |
| `tests/test_portfolio.py` | Demo, trace, env tests |

See also: [project-summary.md](project-summary.md) · [assets/architecture-diagram.md](assets/architecture-diagram.md) · [CONTRIBUTING.md](../CONTRIBUTING.md)

### Artifact files used by parser

| File | Used for |
|------|----------|
| `08_final_itinerary.md` | Summary, stay, logistics, budget, validation sections; day bullets (fallback) |
| `02_research.json` | Day cards with Morning/Afternoon/Evening when present |
| `01_travel_brief.json` | Summary fallback if markdown summary empty |
| `03_lodging.json`, `04_logistics.json`, `05_budget.json` | Not parsed in MVP (markdown sections used instead) |
