# Automations & Multi-Agent Systems — Problem Statement

## Project

**Multi Agent_Tokyo** — a demonstration Travel Planning Multi-Agent System that turns a short natural-language request into a structured trip plan.

This document is the single source of context for the task. Use it when designing agents, orchestration, prompts, and acceptance criteria.

---

## Background

Planning a trip sounds simple at first, but in practice it quickly becomes overwhelming. A single request spans many concerns that are usually handled by different experts or tools.

**Example user request:**

> Plan a 5-day trip to Japan. Tokyo + Kyoto. $3,000 budget. Love food and temples, hate crowds.

To fulfill that well, the system must combine:

| Concern | What “good” looks like |
|--------|-------------------------|
| Intent | Parse goals, constraints, likes/dislikes, dates, and budget |
| Research | Destinations, neighborhoods, attractions, dining |
| Logistics | Inter-city transport, timing, rough travel times |
| Lodging | Areas to stay that fit preferences and budget |
| Budget | Rough cost breakdown and tradeoffs |
| Validation | Final plan still matches the original request |

The point of this project is **not** to ship a production travel product. It is to show how **multiple specialized AI agents** collaborate on a real-world problem that product managers and engineers can reason about clearly.

---

## Objective

Design a **simple Travel Planning Multi-Agent System** that:

1. Accepts a natural-language travel request.
2. Delegates subtasks to specialized agents (or roles).
3. Synthesizes a coherent, human-readable trip plan.
4. Optionally uses external tools (e.g. web search / scraping) for up-to-date information.

Success means demonstrating **clear division of labor**, **handoffs between agents**, and a **final artifact** that respects user constraints—not perfect booking accuracy or live pricing.

---

## Real-World Problem: “AI Travel Planner”

### Input

A user provides a request like:

```
Plan a 5-day trip to Japan. Tokyo + Kyoto. $3,000 budget. Love food and temples, hate crowds.
```

Implicit or explicit fields to extract:

- **Duration** (e.g. 5 days)
- **Destinations** (e.g. Tokyo, Kyoto)
- **Budget** (e.g. $3,000 total)
- **Preferences** (e.g. food, temples)
- **Anti-preferences** (e.g. avoid crowds)
- Optional: dates, party size, pace, mobility, dietary needs

### Output

The system should produce:

1. **Day-by-day outline** — what to do each day, per city
2. **Neighborhood / area suggestions** — where to stay and why
3. **Inter-city logistics** — how to move between cities (e.g. Tokyo ↔ Kyoto)
4. **Budget-aware recommendations** — rough allocation (lodging, food, transport, activities)
5. **Final itinerary** — narrative or structured summary that explicitly ties back to preferences and constraints

### Reference scenario (default demo)

Use the Japan example above as the **canonical test case** for development and demos unless the user specifies otherwise.

---

## Suggested multi-agent decomposition

These roles are guidelines; implementation may merge or split agents as long as responsibilities stay clear.

| Agent / role | Responsibility |
|--------------|----------------|
| **Coordinator / Planner** | Owns the user request, delegates work, merges outputs, runs final validation |
| **Intent parser** | Structured extraction: cities, days, budget, preferences, constraints |
| **Destination researcher** | Attractions, temples, food spots, crowd-aware timing tips |
| **Logistics agent** | Trains/buses between cities, airport transfers, day-trip feasibility |
| **Lodging / neighborhoods** | Where to stay by area; pros/cons vs budget and preferences |
| **Budget agent** | Rough splits and “if over budget” tradeoffs |
| **Validator / critic** | Checks plan against original request; flags gaps or contradictions |

**Orchestration pattern (recommended):** coordinator-led pipeline or hub-and-spoke—coordinator assigns tasks, collects structured or markdown results, then produces one final deliverable.

---

## Constraints and non-goals

### In scope

- Multi-agent workflow with visible specialization
- Readable final itinerary (markdown or JSON + summary)
- Demonstration with the Japan / Tokyo + Kyoto example
- Optional live research via MCP (see below)

### Out of scope (unless explicitly added later)

- Real bookings, payments, or account integrations
- Guaranteed accurate prices or availability
- Visa, insurance, or legal advice
- Mobile app or polished consumer UI (CLI, script, or notebook is sufficient)

### Quality bar

- Plan is **internally consistent** (days add up, cities match request, budget discussed)
- Preferences and anti-preferences are **addressed in prose**, not ignored
- Crowd avoidance is reflected in **timing or venue choices** where possible
- Failures are **explained** (e.g. “could not verify train fare; using typical range”)

---

## Available tooling (MCP)

The workspace is configured with MCP servers agents may use for research:

| Server | Purpose |
|--------|---------|
| **Bright Data** (`user-brightdata-mcp`) | Web search (`search_engine`, `search_engine_batch`) and page scrape (`scrape_as_markdown`, `scrape_batch`, `discover`) for current travel info |
| **Alpha Vantage** (`user-alphavantage`) | Financial/market data APIs — **not required** for travel planning unless repurposed for budget FX estimates |

Prefer Bright Data when agents need **current** attraction hours, routes, or neighborhood context. Cache or summarize scraped content before passing large blobs between agents.

---

## Deliverables (implementation)

Minimum artifacts for this repository:

| Artifact | Description |
|----------|-------------|
| **Multi-agent runtime** | Code or Cursor workflow that runs the agent graph on a user prompt |
| **Agent definitions** | Prompts and/or modules per role (coordinator + specialists) |
| **Example run** | One completed plan for the canonical Japan request |
| **This document** | `docs/problemstatement.md` — kept in sync if scope changes |

Optional: `README.md` with how to run; sample output under `docs/` or `examples/`.

---

## Acceptance criteria

The task is complete when:

- [x] A user can submit the canonical request (or equivalent) and receive a structured trip plan.
- [x] At least **three distinct agent roles** contribute before the final merge (e.g. intent, research, logistics, budget, validation).
- [x] Output includes **day-by-day outline**, **stay areas**, **inter-city logistics**, and **budget discussion**.
- [x] Final output **references** food, temples, and crowd avoidance from the example request.
- [x] Coordinator or validator step confirms alignment with constraints (or lists gaps).

*Verified Phase 2 — live run `596da9cd4964`, golden copy in `examples/canonical-japan/`, mock tests in `tests/`.*

---

## Example final output shape (template)

```markdown
# Trip plan: 5 days — Tokyo & Kyoto

## Summary
- Budget target: $3,000 (rough breakdown: …)
- Themes: food, temples; avoid crowds where possible

## Day-by-day
### Day 1 — Tokyo
…

## Where to stay
### Tokyo: …
### Kyoto: …

## Logistics
- Tokyo → Kyoto: …

## Budget notes
…

## Validation
- Matches request: yes / partial — …
```

---

## Open questions (track as scope evolves)

- Runtime: pure Cursor agents vs Python/TypeScript orchestration vs Cursor SDK
- Structured JSON schema for inter-agent messages vs markdown-only handoffs
- Whether to pin demo to **only** Tokyo/Kyoto or support arbitrary cities in v1

---

## Revision log

| Date | Change |
|------|--------|
| 2026-05-20 | Expanded from initial draft; added agents, MCP, deliverables, acceptance criteria |
