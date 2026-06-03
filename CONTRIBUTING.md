# Contributing

Thank you for your interest in **Multi Agent Tokyo**. This project is a coordinator-led multi-agent travel planner with an additive Streamlit voice UI. Contributions should preserve the existing pipeline contract (`plan_trip_sync` / `run_trip`).

---

## Setup

```bash
git clone <repo-url>
cd Multi\ Agent_Tokyo
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev,voice]"
cp .env.example .env
```

Set `GROQ_API_KEY` and `GEMINI_API_KEY` in `.env` only if you plan to run **live** pipeline tests or manual CLI/UI generation.

---

## Running tests

**Default (safe — no API quota):**

```bash
pytest tests/test_schemas.py tests/test_client.py tests/test_config.py -q
pytest tests/test_voice_app.py tests/test_portfolio.py -q
pytest tests/test_pipeline_integration.py tests/test_acceptance.py -q
```

| Suite | Uses network? |
|-------|----------------|
| `test_voice_app.py`, `test_portfolio.py` | No |
| `test_pipeline_integration.py` | No (mocked LLM) |
| `test_acceptance.py` | No (reads `examples/canonical-japan/`) |

**Avoid** running broad live CLI/UI plans repeatedly — Gemini free tier is ~20 requests/day.

---

## Style expectations

- **Minimal diffs** — match existing naming, typing (`Optional[]` on Python 3.9), and module layout.
- **Additive UI** — new presentation code belongs under `app/`; do not rewrite `orchestrator/pipeline.py` without discussion.
- **No new orchestration frameworks** — no LangGraph, `workflows/`, or parallel planner abstractions.
- **Tests** for real behavior; avoid trivial assertions.
- **Docs** — update README and relevant `docs/` when changing install, env vars, or demo mode.

---

## Branch guidance

1. Fork / branch from `main`.
2. One logical change per PR (feature, fix, or docs).
3. Ensure `pytest` passes for mock suites before opening a PR.
4. Note quota impact in the PR description if you add live API tests.

---

## Adding a new agent safely

1. Define or extend schemas in `llm/schemas.py`.
2. Add agent class under `agents/` and prompt under `agents/prompts/`.
3. Register provider in `orchestrator/config.py` (`AGENT_PROVIDERS`).
4. Wire the step in `orchestrator/pipeline.py` (maintain trace via `RunState.trace`).
5. Add fixture JSON/MD under `tests/fixtures/` and extend `mock_completion_fn` in `tests/conftest.py`.
6. Update `docs/architecture.md` and artifact list in `RunState.ARTIFACTS` if new files are written.

Do **not** change `PlanTripResult` fields without updating UI parsers and tests.

---

## Quota awareness

| Provider | Typical cost per full plan |
|----------|----------------------------|
| Groq | ~6 calls |
| Gemini | ~2 calls |

Use **demo mode** in the Streamlit app (`examples/canonical-japan/`) for UI work and recordings.

---

## Questions

Open an issue with:

- What you want to change
- Whether it touches the pipeline or UI only
- How you tested (mock vs live)

See [docs/project-summary.md](docs/project-summary.md) for project context.
