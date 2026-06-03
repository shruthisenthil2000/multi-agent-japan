# 5-Minute Demo Script

Use this for LinkedIn recordings, recruiter screens, or portfolio walkthroughs.

**Time:** ~5 minutes  
**Prereq:** `pip install -e ".[voice]"` and `streamlit run app/voice_agent.py`

---

## 0:00 — Hook (30s)

> "This is a multi-agent travel planner. You talk to it like a copilot; behind the scenes, Groq and Gemini specialists research destinations, lodging, logistics, budget, then merge and validate a full itinerary."

Show title screen: **Voice Travel Copilot**.

---

## 0:30 — Demo mode (no API keys) (60s)

1. Open **sidebar** → enable **Demo mode**.
2. Click **Use demo itinerary**.
3. Point to **Trip Planner** panel:
   - Summary expander
   - Day cards with Morning / Afternoon / Evening
   - Budget, Logistics, Stay sidebars
   - Validation metric
4. Expand **Agent timeline** — show `trace.jsonl` steps from canonical run.

> "Demo mode uses committed example data — zero API cost, perfect for interviews."

---

## 1:30 — Conversation flow (90s)

1. Click **Clear** (or refresh).
2. Disable demo mode (optional if you have keys).
3. Click example prompt: **"Japan trip"**.
4. Show slot checklist:
   - Destination ✅
   - Duration ❌
   - Budget ❌
5. Reply: **"5 days, Tokyo and Kyoto, under $3000, love food"**.
6. Show checklist turn green; **Generate trip** enables.

> "The UI never calls the LLM pipeline until required slots are filled — that saves quota and avoids bad requests."

---

## 3:00 — Live generate (optional, 90s)

*Skip if no API keys or low Gemini quota.*

1. Click **Generate trip**.
2. Watch staged progress:
   - Parsing request…
   - Running specialists…
   - Merging itinerary…
   - Validating plan…
3. When complete, scroll day cards and sidebars.

> "Same orchestrator as the CLI — `plan_trip_sync` — no separate workflow engine."

---

## 4:00 — Voice + export (60s)

1. Click **Speak** (if mic available) or type a short refinement.
2. **Export Markdown** and **Export PDF** download buttons.
3. Mention sidebar env check (Groq/Gemini/voice/PDF status).

---

## 4:45 — Close (15s)

> "Architecture stays coordinator-led: intent → parallel Groq specialists → Gemini budget → merge → validate. Phase L+ adds live data via MCP. Repo link in description."

**CTA:** GitHub link, `streamlit run` command, screenshot of two-panel UI.

---

## Troubleshooting on camera

| Issue | Say / do |
|-------|----------|
| No API keys | Use demo mode only |
| Mic fails | "Voice is optional — text works fully" |
| Slow plan | "Typical run 30–60s; trace shows per-agent timing" |
| Gemini quota | "Demo mode for repeat takes" |

---

## Screenshot checklist

- [ ] Two-panel UI (chat + itinerary)
- [ ] Slot checklist with ✅/❌
- [ ] Day card with Morning/Afternoon/Evening
- [ ] Agent timeline expander
- [ ] Sidebar demo + env status
