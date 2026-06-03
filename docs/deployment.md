# Deployment Guide

Deploy the **Voice Travel Copilot** (Streamlit) and the CLI planner without changing the multi-agent pipeline.

---

## Prerequisites

- Python **3.9+**
- API keys for **live** planning: `GROQ_API_KEY`, `GEMINI_API_KEY`
- Optional: microphone (voice), `pip install -e ".[voice]"`

---

## Local setup

```bash
git clone <repo-url>
cd Multi\ Agent_Tokyo
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[voice]"   # core + Streamlit + speech + PDF
cp .env.example .env
```

Edit `.env`:

```env
GROQ_API_KEY=...
GEMINI_API_KEY=...
RATE_LIMIT_ENABLED=true
```

Run UI:

```bash
streamlit run app/voice_agent.py
```

Run CLI:

```bash
plan-trip "Plan a 5-day trip to Tokyo and Kyoto under $3000."
```

---

## Demo mode (no API keys)

For portfolio recordings or offline demos:

1. Open the app sidebar.
2. Enable **Demo mode**.
3. Click **Use demo itinerary**.

Loads `examples/canonical-japan/` — **no** `plan_trip_sync`, Groq, or Gemini calls.

---

## Voice setup

| Component | Install | Notes |
|-----------|---------|-------|
| STT | `speechrecognition` | Google Web API; needs network |
| TTS | `pyttsx3` | Optional read-aloud |
| Mic | OS permissions | macOS: System Settings → Privacy → Microphone |

---

## Streamlit Cloud

1. Push repo to GitHub.
2. [share.streamlit.io](https://share.streamlit.io) → New app.
3. Main file: `app/voice_agent.py`
4. Python 3.9–3.11 recommended.
5. Add secrets in the dashboard:

   ```toml
   GROQ_API_KEY = "..."
   GEMINI_API_KEY = "..."
   ```

6. `requirements.txt` alternative (if not using pyproject):

   ```
   -e .[voice]
   ```

**Tip:** Use **Demo mode** on Streamlit Cloud if you do not want to expose API quota during public demos.

---

## Docker

Build and run (from repo root):

```bash
docker build -t voice-travel-copilot .
docker run -p 8501:8501 --env-file .env voice-travel-copilot
```

Open `http://localhost:8501`.

Pass secrets via `--env-file` or `-e GROQ_API_KEY=...`.

---

## Environment variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `GROQ_API_KEY` | Live plan | Intent, research, lodging, logistics, merge |
| `GEMINI_API_KEY` | Live plan | Budget, validator |
| `GROQ_MODEL` | No | Default `llama-3.3-70b-versatile` |
| `GEMINI_MODEL` | No | Default `gemini-3-flash` |
| `RATE_LIMIT_ENABLED` | No | Default `true` |
| `DATA_MODE` | No | `llm_only` (Phase 1) |

Startup checks run in the app sidebar via `app/env_check.py`.

---

## Quota considerations

| Provider | ~calls per full plan | Free-tier note |
|----------|----------------------|----------------|
| Groq | ~6 | RPM 30 |
| Gemini | ~2 | **RPD ~20** (~10 plans/day) |

Regenerate and retries consume additional quota. Prefer **demo mode** for repeated portfolio walkthroughs.

---

## Production notes

- Streamlit is single-user oriented; for multi-tenant production consider a thin FastAPI wrapper around `orchestrator.api.run_trip` plus a separate frontend.
- Do not commit `.env` or API keys.
- `runs/` is gitignored; mount a volume in Docker if you need persistent artifacts.

---

## Related docs

- [voice-agent.md](voice-agent.md) — UI architecture
- [demo-script.md](demo-script.md) — 5-minute walkthrough
- [architecture.md](architecture.md) — Pipeline design
- [project-summary.md](project-summary.md) — Recruiter overview
- [assets/README.md](assets/README.md) — Screenshot capture guide
