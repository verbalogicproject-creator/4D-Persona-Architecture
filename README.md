# Soccer-AI ⚽

## Reference Implementation of the 4D Persona Architecture

**Author**: Eyal Nof
**Date**: December 28, 2025

> *"The AI doesn't play a character. It lives one."*

---

## 🚀 What's New: A Novel AI Architecture

This project demonstrates the **4D Persona Architecture**, a paradigm shift in how AI personas are designed:

| Traditional | 4D Persona |
|-------------|------------|
| "Be enthusiastic" | Enthusiasm *derived* from winning streak |
| Static text prompt | Dynamic 4D coordinate |
| Actor in costume | Character inhabiting reality |

### The Four Dimensions

```
P(t) = (x, y, z, t)

x = Emotional   → Mood derived from ACTUAL match results
y = Relational  → Position in club→rivals→legends knowledge graph
z = Linguistic  → Regional dialect (Scouse, Geordie, Cockney)
t = Temporal    → Evolution trajectory through time
```

### Embodied RAG

Traditional RAG retrieves facts. **Embodied RAG computes feelings.**

When Arsenal loses three matches, the AI fan isn't *told* to be frustrated—it *is* frustrated, because the data says so.

📄 **[Full Specification](docs/architecture/4D-PERSONA-ARCHITECTURE.md)** | 📝 **[Blog Post](docs/BLOG-embodied-rag.md)** | 📚 **[arXiv Paper](docs/arxiv/4d-persona-architecture.tex)**

---

## What Is Soccer-AI?

An emotionally intelligent football companion that **feels the game with you**.

- **Supports your club** with authentic fan emotion
- **Speaks proper football** (match, nil, pitch - never "soccer")
- **Knows rivalries** and won't praise your enemies
- **Predicts matches** with 62.9% accuracy
- **Remembers legends and moments** that define club identity

---

## Quick Start

### Backend

```bash
cd backend
pip install fastapi uvicorn anthropic aiohttp python-dotenv httpx
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Access: http://localhost:5173

---

## Features

### 🎭 Dynamic Mood System (Dimension X)
Mood computed from **actual database results**:
```
Man City:  euphoric 🎉 (WWDWW) - "Unstoppable!"
Arsenal:   anxious  😰 (WWDLD) - "Need to pick it up!"
Liverpool: frustrated 😤 (DLDLW) - "Getting worried!"
```

### ⚔️ Rivalry Banter (Dimension Y)
Knowledge graph activates relationship-specific behavior:
- Arsenal + "Spurs?" → Full North London Derby mode
- 20+ rivalries with intensity levels

### 🗣️ Local Dialect (Dimension Z)
Regional voice identity:
- **Liverpool**: Scouse ("la", "sound", "boss")
- **Newcastle**: Geordie ("howay", "canny")
- **West Ham**: Cockney ("leave it out")

### ⏱️ Temporal Continuity (Dimension T)
- Conversation memory
- Persona trajectory tracking
- Momentum prediction

---

## Architecture

```
React Frontend
      │
      ▼
FastAPI Backend ──────────────────────┐
      │                               │
      ▼                               ▼
┌─────────────────────────────────────────────────┐
│              4D PERSONA ENGINE                   │
├────────────┬───────────┬───────────┬────────────┤
│ EMOTIONAL  │ RELATIONAL│ LINGUISTIC│  TEMPORAL  │
│ (X-axis)   │ (Y-axis)  │ (Z-axis)  │  (T-axis)  │
│            │           │           │            │
│ Match DB   │ KG Graph  │ Dialect DB│ History    │
│ Form calc  │ Traverse  │ Voice map │ Trajectory │
│ Mood derive│ Activate  │ Inject    │ Momentum   │
└────────────┴───────────┴───────────┴────────────┘
                    │
                    ▼
            Dynamic System Prompt
                    │
                    ▼
              Claude Haiku
```

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/fan_enhancements.py` | Emotional dimension (X) |
| `backend/rag.py` | Relational dimension (Y) |
| `backend/ai_response.py` | 4D synthesis |
| `docs/architecture/4D-PERSONA-ARCHITECTURE.md` | Full spec |
| `docs/arxiv/4d-persona-architecture.tex` | Academic paper |

---

## Citation

```bibtex
@article{nof2025persona4d,
  title={4D Persona Architecture: A Dimensional Model for Embodied AI Agents},
  author={Nof, Eyal},
  year={2025},
  note={Reference implementation: Soccer-AI}
}
```

---

## License

MIT License

---

**Created by Eyal Nof** | **December 2025**

*Fan at heart. Architect by discovery.* ⚽
