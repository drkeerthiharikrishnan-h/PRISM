# PRISM — Persona-Driven Research Intelligence System

> **Gladstone Institute × Cerebral Valley Hackathon 2026**  
> *"One query. Four expert lenses."*

PRISM solves the "flat LLM response" problem in biomedical research. Standard AI tools return identical answers regardless of who is asking. PRISM routes the same query through **four distinct professional lenses** — each hitting different databases, extracting different evidence, and synthesising a role-appropriate response.

---

## Demo

**Query:** *"What do I need to know about imatinib and its target ABL1?"*

| 🧪 Medicinal Chemist | 🔬 Pathologist |
|---|---|
| IC50 ≈ 0.1 µM vs ABL1 · PDB 1IEP (2.1 Å DFG-out) · 2-phenylaminopyrimidine scaffold | T315I gatekeeper mutation → abolishes imatinib binding · switch to ponatinib |

| 🧬 Cell Biologist | 💻 Computational Biologist |
|---|---|
| Locks inactive conformation → halts STAT5/CrkL phosphorylation · BCR-ABL → RAS/MAPK/PI3K | PDB 1IEP + AlphaFold AF-P00519-F1 · UniProt P00519 (T315 gatekeeper) · ChEMBL ~N bioactivities |

---

## Architecture

```
Query → [Step 1] LLM parse (entity + target)
      → [Step 2] HTTP ID resolve (PubChem · ChEMBL · UniProt)
      → [Step 3] Persona YAML plan (which databases per role)
      → [Step 4] Parallel connector fetch (8 open databases)
      → [Step 5] 4× streaming Claude synthesis
```

**Total LLM calls: 5–6** (1 parse + optional detect + 4 synthesis)  
**All databases open:** PubMed · ChEMBL · PDB · UniProt · PubChem · ClinVar · Reactome · AlphaFold

---

## Quickstart

```bash
# 1. Clone
git clone git@github.com:drkeerthiharikrishnan-h/PRISM.git
cd PRISM

# 2. Install dependencies (requires uv)
uv sync

# 3. Configure
cp .env.example .env
# Edit .env — add your ANTHROPIC_API_KEY and NCBI_API_KEY

# 4. Run
uv run uvicorn main:app --reload

# 5. Open http://localhost:8000
```

---

## Adding a New Persona

No Python needed. Create `personas/your_role.yaml`:

```yaml
name: Regulatory Specialist
emoji: "📋"
color: "#ef4444"
connectors:
  - name: pubmed
    params:
      keywords: [FDA approval, clinical trial, safety, adverse events]
extract_fields: [regulatory_status, safety_profile]
sections: [Regulatory status, Safety profile, Open questions]
synthesis_prompt: |
  You are a regulatory affairs specialist...
```

The system picks it up automatically — no code changes.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python, async) |
| Streaming | Server-Sent Events (SSE) |
| Frontend | HTML + TailwindCSS CDN + Vanilla JS |
| LLM | Claude Sonnet 4.6 (Anthropic) |
| Package manager | uv |

---

## Team

Built at the **Gladstone Institute × Cerebral Valley Built with Claude: Life Sciences Hackathon (July 2026)**  
by **Keerthi Hari Krishnan** (Biomedical SME) and **Balaji** (Engineering).
