# System Architecture Diagram

Canonical diagram for README, portfolios, and submissions.  
Render on GitHub or any Mermaid-compatible viewer.

---

## End-to-end flow

```mermaid
flowchart TB
    User([User])

    subgraph VoiceUI["Voice UI — Streamlit (app/)"]
        VA[voice_agent.py]
        SP[speech.py · STT/TTS]
        CM[conversation.py · slot filling]
        UI[itinerary_ui.py · rich cards]
        DM[demo_data.py · offline demo]
    end

    subgraph API["Orchestrator API"]
        RT[orchestrator.api.run_trip]
        PTS[orchestrator.pipeline.plan_trip_sync]
    end

    subgraph Pipeline["Multi-agent pipeline"]
        IP[Intent Parser · Groq]
        PAR{{Parallel specialists · Groq}}
        DR[Destination Researcher]
        LO[Lodging]
        LG[Logistics]
        BU[Budget · Gemini]
        MG[Merge · Groq]
        VA2[Validator · Gemini]
    end

    subgraph Artifacts["Run artifacts runs/run_id/"]
        T[trace.jsonl]
        MD[08_final_itinerary.md]
        JSON[01–07 JSON / MD artifacts]
    end

    User -->|voice or text| VA
    VA --> SP
    VA --> CM
    CM -->|composed NL request| RT
    RT --> PTS
    PTS --> IP --> PAR
    PAR --> DR
    PAR --> LO
    PAR --> LG
    PAR --> BU --> MG --> VA2
    PTS --> Artifacts
    Artifacts --> UI
    DM -.->|demo only, no API| UI
    VA --> UI
    T --> UI
```

---

## Layer responsibilities

| Layer | Location | Role |
|-------|----------|------|
| Voice UI | `app/voice_agent.py` | Chat, slots, generate, exports |
| Conversation | `app/conversation.py` | Rule-based slot filling before API |
| API wrapper | `orchestrator/api.py` | `run_trip()` → `plan_trip_sync()` |
| Pipeline | `orchestrator/pipeline.py` | Coordinator sequence, no LangGraph |
| Agents | `agents/*` | Specialist LLM calls + prompts |
| Schemas | `llm/schemas.py` | Pydantic contracts between steps |

---

## What is intentionally excluded

- LangGraph / `graph.invoke()`
- `workflows/` orchestration packages
- Live Places/Booking APIs (Phase L+ in [implementation-plan.md](../implementation-plan.md))

---

## Related docs

- [architecture.md](../architecture.md) — detailed component design
- [voice-agent.md](../voice-agent.md) — UI behavior
- [deployment.md](../deployment.md) — run & deploy
