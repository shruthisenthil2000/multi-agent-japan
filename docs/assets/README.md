# Portfolio assets

Add screenshots and diagrams here for README and LinkedIn posts.  
**Do not commit API keys or personal data in images.**

---

## Required screenshots (placeholders)

Capture these from a local run of `streamlit run app/voice_agent.py` (1440×900 or 1920×1080 recommended).

| File | What to capture | Suggested filename |
|------|-----------------|------------------|
| **Homepage** | Full two-panel UI with onboarding visible | `homepage.png` |
| **Slot filling** | Left panel checklist with mix of ✅ and ❌ | `slot-filling.png` |
| **Planning progress** | `st.status` stages during live generate | `planning-progress.png` |
| **Itinerary output** | Right panel: day cards + budget/logistics sidebars | `itinerary-output.png` |
| **Demo mode** | Sidebar with Demo mode on + loaded itinerary | `demo-mode.png` |

### How to capture

1. macOS: `Cmd + Shift + 4` → select window.
2. Save PNGs into this folder (`docs/assets/`).
3. Update root [README.md](../../README.md) image tags (uncomment and set paths).

Example markdown for README:

```markdown
![Homepage](docs/assets/homepage.png)
```

---

## Diagram (no screenshot needed)

Use the Mermaid source in [architecture-diagram.md](architecture-diagram.md).  
GitHub renders Mermaid in markdown automatically.

---

## Optional assets

| Asset | Purpose |
|-------|---------|
| `demo.gif` | Short screen recording for README hero |
| `architecture.png` | Export Mermaid diagram from [mermaid.live](https://mermaid.live) |

---

## .gitignore note

Large binary assets are fine to commit for portfolio repos. If files exceed GitHub limits, host on a CDN and link from README.
