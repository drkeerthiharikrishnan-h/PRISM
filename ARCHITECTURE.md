# Facet — Architecture & System Design

> **Persona-Driven Research Intelligence System**  
> Gladstone Institute × Cerebral Valley Built with Claude: Life Sciences Hackathon 2026

---

## Table of Contents

1. [Problem & Solution](#1-problem--solution)
2. [High-Level Architecture](#2-high-level-architecture)
3. [The 5-Step Pipeline](#3-the-5-step-pipeline)
4. [Persona System](#4-persona-system)
5. [External Database Connections](#5-external-database-connections)
6. [Streaming Architecture (SSE)](#6-streaming-architecture-sse)
7. [User Identity & Persona Detection](#7-user-identity--persona-detection)
8. [Caching Strategy](#8-caching-strategy)
9. [File & Module Reference](#9-file--module-reference)
10. [Data Flow Diagrams](#10-data-flow-diagrams)
11. [LLM Call Budget](#11-llm-call-budget)
12. [Tech Stack Summary](#12-tech-stack-summary)
13. [Running the System](#13-running-the-system)

---

## 1. Problem & Solution

### The Problem — "Flat" LLM Responses

Standard AI tools return the **same answer** to everyone, regardless of professional role. If a Medicinal Chemist and a Pathologist both ask:

> *"What do I need to know about imatinib and its target ABL1?"*

They receive identical generic text. But their actual needs are completely different:

| Professional | What they actually need |
|---|---|
| 🧪 Medicinal Chemist | IC50 potency numbers, 3D co-crystal structures, scaffold SAR data |
| 🔬 Pathologist | Which ABL1 mutations cause resistance, clinical significance, treatment switches |
| 🧬 Cell Biologist | Which pathways ABL1 sits in, how imatinib disrupts downstream signaling |
| 💻 Computational Biologist | PDB structures, AlphaFold predictions, bioactivity datasets for ML |

### The Solution — Persona-Driven Orchestration

Facet intercepts every query and routes it through **four professional lenses simultaneously**. The user's role determines:
- Which databases are queried
- Which fields are extracted
- How the answer is structured and synthesised

The same query → four completely different expert responses, all grounded in real open biomedical data.

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER BROWSER                               │
│                                                                     │
│   Landing Page         Query Screen              4-Panel View       │
│  ┌──────────┐         ┌────────────────┐        ┌────┬────┐        │
│  │ Role     │──────►  │ Query Input    │──────►  │ 🧪 │ 🔬 │        │
│  │ Cards    │         │ [▶ Run][Demo]  │  SSE   │────┼────│        │
│  └──────────┘         └────────────────┘ stream │ 🧬 │ 💻 │        │
│                                                  └────┴────┘        │
└────────────────────────────┬────────────────────────────────────────┘
                             │  HTTP POST /api/query
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        FASTAPI BACKEND                              │
│                                                                     │
│  main.py — Routes + SSE streaming endpoint                          │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    orchestrator.py                          │   │
│  │                                                             │   │
│  │  Step 1      Step 2       Step 3      Step 4     Step 5    │   │
│  │  [Parse] → [Resolve] → [Plan] → [Retrieve] → [Synthesise] │   │
│  │  1 LLM    HTTP only   YAML cfg   8 APIs     4 LLM calls   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────┐    ┌─────────────────────────────────────┐   │
│  │ entity_resolver  │    │            connectors/              │   │
│  │ • parse_query    │    │  pubmed  chembl  pdb    uniprot     │   │
│  │ • resolve_ids    │    │  pubchem clinvar reactome alphafold │   │
│  │ • detect_persona │    └─────────────────────────────────────┘   │
│  └──────────────────┘                                              │
│                                                                     │
│  ┌──────────────────┐    ┌──────────────────────────────────────┐  │
│  │  personas/*.yaml │    │           cache/*.json               │  │
│  │  4 config files  │    │   pre-fetched demo data              │  │
│  └──────────────────┘    └──────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
           ┌─────────────────┼──────────────────────┐
           ▼                 ▼                       ▼
    ┌─────────────┐  ┌──────────────┐      ┌──────────────────┐
    │ Claude API  │  │ Open Biomedical│     │   Local Cache    │
    │ (Anthropic) │  │  Databases    │      │  (JSON files)    │
    │             │  │               │      │                  │
    │ Haiku 4.5   │  │  PubMed       │      │ imatinib_abl1    │
    │ (parse +    │  │  ChEMBL       │      │ .json            │
    │  detect)    │  │  PDB/RCSB     │      │                  │
    │             │  │  UniProt      │      │ (pre-fetched     │
    │ Sonnet 4.6  │  │  PubChem      │      │  before demo)    │
    │ (synthesis  │  │  ClinVar      │      └──────────────────┘
    │  × 4)       │  │  Reactome     │
    └─────────────┘  │  AlphaFold DB │
                     └──────────────┘
```

---

## 3. The 5-Step Pipeline

Every query runs through exactly 5 steps. Steps 1 and 5 call Claude. Steps 2, 3, 4 are pure code — no LLM.

### Step 1 — Entity Parser
**File:** `entity_resolver.py::parse_query()`  
**LLM:** 1 call (Claude Haiku 4.5 — fast, cheap)  
**Cached:** Yes — MD5 hash of query string

Takes the user's free-text query and extracts the key biomedical entities:

```
Input:  "What do I need to know about imatinib and its target ABL1?"

Output: {
  "entity": "imatinib",
  "target": "ABL1",
  "entity_type": "drug"
}
```

Results are cached to disk so repeat queries cost nothing.

---

### Step 2 — ID Resolver
**File:** `entity_resolver.py::resolve_ids()`  
**LLM:** None — pure HTTP  
**Speed:** ~2–4 seconds (4 parallel API calls)

Maps human-readable names to the exact database identifiers used by each connector. Runs all 4 lookups in parallel via `asyncio.gather()`:

```
Input:  entity="imatinib", target="ABL1"

Parallel HTTP calls:
  PubChem  → /compound/name/imatinib/cids/JSON     → CID: 5291
  ChEMBL   → /molecule/search?q=imatinib           → CHEMBL941
  UniProt  → /search?query=gene:ABL1&reviewed=true → P00519
  ChEMBL   → /target/search?q=ABL1                 → CHEMBL1862

Output: {
  "drug_pubchem":   "5291",
  "drug_chembl":    "CHEMBL941",
  "target_uniprot": "P00519",
  "target_chembl":  "CHEMBL1862"
}
```

---

### Step 3 — Persona Plan
**File:** `orchestrator.py::get_persona_plan()`  
**LLM:** None — YAML config lookup  
**Speed:** Instant (<1ms)

Reads the YAML config for the requested persona(s) and builds a list of connector calls with the resolved IDs substituted in:

```
Input:  persona="medicinal_chemist", entity_ids={...}

Reads:  personas/medicinal_chemist.yaml

Output: [
  { connector: "chembl",  params: { query_type: "activity", types: ["IC50","Ki"] } },
  { connector: "pdb",     params: { query_type: "ligand_search" } },
  { connector: "pubchem", params: { query_type: "scaffold" } },
  { connector: "pubmed",  params: { keywords: ["SAR","co-crystal","IC50"] } }
]
```

---

### Step 4 — Retrieve
**File:** `orchestrator.py::retrieve_for_persona()`  
**LLM:** None — parallel HTTP calls  
**Speed:** ~5–10 seconds (connectors run concurrently per persona)

Calls every connector in the plan simultaneously. Each connector returns a structured Python dict — no LLM involved at this stage. Numbers, IDs, and metadata are extracted by plain field mapping.

```
Input:  connector plan from Step 3

Parallel HTTP calls to real databases:
  ChEMBL   → 10 IC50 activity records for imatinib vs ABL1
  PDB/RCSB → 5 crystal structure entries (1IEP, 2HYY, ...)
  PubChem  → SMILES, molecular formula, MW for imatinib
  PubMed   → 5 most-relevant paper abstracts

Output (structured evidence dict):
  {
    "chembl":  { "activities": [...], "count": 100 },
    "pdb":     { "structures": [{"pdb_id": "1IEP", "resolution": 2.1, ...}] },
    "pubchem": { "cid": "5291", "canonical_smiles": "...", "molecular_formula": "C29H31N7O" },
    "pubmed":  { "abstracts": [{"pmid": "...", "title": "...", "abstract": "..."}] }
  }
```

For **4-panel compare mode**, all 4 personas run Step 4 concurrently — 8 databases queried simultaneously.

---

### Step 5 — Synthesise & Stream
**File:** `orchestrator.py::synthesize_stream()`  
**LLM:** 1 streaming call per persona (Claude Sonnet 4.6)  
**Speed:** ~15–30 seconds streaming (tokens appear in real time)

Takes the structured evidence from Step 4 and sends it to Claude with a persona-specific system prompt. The model writes a sectioned, cited response. Tokens stream directly to the browser as they are generated.

```
Input:
  system: persona synthesis prompt (from YAML)
  user:   {
    "question": "What do I need to know about imatinib and ABL1?",
    "structured_evidence": "[E1] CHEMBL: {activities...}\n[E2] PDB: {structures...}\n...",
    "abstracts": "[E5] PUBMED PMID:123: Title. Abstract..."
  }

Output (streamed tokens → browser):
  ## SAR Summary
  Imatinib shows IC50 ≈ 0.1 µM against ABL1 [E1]. The 2-phenylaminopyrimidine
  core anchors in the ATP pocket while the N-methylpiperazine tail improves
  aqueous solubility [E3]...

  ## Key Structures
  PDB 1IEP: ABL1 kinase + imatinib at 2.1 Å resolution, DFG-out inactive
  conformation [E2]...
```

---

## 4. Persona System

### What a Persona Is

A persona is a single YAML file in `personas/` that completely defines one professional lens. Adding a new persona = adding one file, zero code changes.

### YAML Schema

```yaml
name: Medicinal Chemist          # Display name
emoji: "🧪"                       # UI icon
color: "#0ea5e9"                  # Panel accent color

connectors:                       # Which databases to query + how
  - name: chembl
    params:
      query_type: activity
      standard_types: [IC50, Ki, Kd]
  - name: pdb
    params:
      query_type: ligand_search
  - name: pubchem
    params:
      query_type: scaffold
  - name: pubmed
    params:
      keywords: [SAR, structure-activity, co-crystal, IC50, analogue]

extract_fields:                   # Logical fields this persona cares about
  - binding_affinity
  - structures
  - scaffold
  - sar_notes

sections:                         # Section headings in the response
  - SAR summary
  - Key structures
  - Bioactivity
  - Open questions

synthesis_prompt: |               # System prompt injected into Claude
  You are a senior medicinal chemist responding to a colleague...
  Cite every claim as [E1], [E2]...
```

### The Four Personas

| Persona | Databases | Unique Focus |
|---|---|---|
| 🧪 Medicinal Chemist | ChEMBL · PDB · PubChem · PubMed | Potency numbers · 3D structures · scaffold chemistry · SAR |
| 🔬 Pathologist | ClinVar · PubMed | Resistance mutations · clinical significance · diagnostic markers |
| 🧬 Cell / Molecular Biologist | Reactome · UniProt · PubMed | Biological pathways · mechanism of action · protein interactions |
| 💻 Computational Biologist | PDB · AlphaFold · UniProt · ChEMBL · PubMed | Crystal structures · predicted structures · sequence · ML datasets |

### Database Coverage Per Persona

```
              ChEMBL  PDB  PubChem  ClinVar  Reactome  UniProt  AlphaFold  PubMed
Chem. Chemist   ✅     ✅     ✅                                              ✅
Pathologist                          ✅                                      ✅
Cell Biologist                                  ✅         ✅                ✅
Comp. Biologist ✅     ✅                                   ✅       ✅       ✅
```

Note: PubMed is used by all personas but with **different search keywords**, so even the papers retrieved differ by role.

---

## 5. External Database Connections

All databases are **open and free**. No paid APIs. Two API keys total:  
- **Anthropic API key** — for Claude LLM calls  
- **NCBI API key** — for PubMed and ClinVar rate limit (10 req/sec vs 3 req/sec without key)

### PubMed
**Connector:** `connectors/pubmed.py`  
**API:** NCBI E-utilities REST  
**Base URL:** `https://eutils.ncbi.nlm.nih.gov/entrez/eutils`  
**Auth:** Optional free NCBI key (increases rate limit)  
**What we fetch:** Top 5 most-relevant paper titles + abstracts  
**Used by:** All 4 personas (with different keyword searches per role)

```
GET /esearch.fcgi?db=pubmed&term=imatinib+AND+ABL1+AND+(SAR+OR+co-crystal)
  → List of PMIDs

GET /efetch.fcgi?db=pubmed&id=<pmids>&retmode=xml&rettype=abstract
  → XML containing title + abstract text
```

---

### ChEMBL
**Connector:** `connectors/chembl.py`  
**API:** EBI ChEMBL REST API  
**Base URL:** `https://www.ebi.ac.uk/chembl/api/data`  
**Auth:** None (fully open)  
**What we fetch:**
- *Medicinal Chemist:* IC50/Ki/Kd activity records for the drug vs target
- *Computational Biologist:* Full bioactivity dataset count for ML training

```
GET /activity.json
  ?molecule_chembl_id=CHEMBL941
  &target_chembl_id=CHEMBL1862
  &standard_type__in=IC50,Ki,Kd
  → [{standard_type, standard_value, standard_units, assay_description}, ...]
```

---

### PDB / RCSB
**Connector:** `connectors/pdb.py`  
**APIs:** RCSB Search API + RCSB Data API  
**Base URLs:**
- `https://search.rcsb.org/rcsbsearch/v2/query` (search)
- `https://data.rcsb.org/rest/v1/core/entry/{id}` (entry details)

**Auth:** None  
**What we fetch:** 3D crystal structure entries — PDB ID, resolution, experimental method, title  
**Used by:** Medicinal Chemist + Computational Biologist

```
POST /rcsbsearch/v2/query  (full-text or sequence search)
  → ["1IEP", "2HYY", "6HD6", ...]

GET /rest/v1/core/entry/1IEP
  → { title, resolution: 2.1, method: "X-RAY DIFFRACTION" }
```

---

### UniProt
**Connector:** `connectors/uniprot.py`  
**API:** UniProt REST API  
**Base URL:** `https://rest.uniprot.org/uniprotkb`  
**Auth:** None  
**What we fetch:**
- *Cell Biologist:* Protein function text, GO terms, interaction annotations
- *Computational Biologist:* Amino acid sequence length, binding site positions, domain architecture

```
GET /P00519.json?fields=cc_function,go,sequence,ft_binding,ft_domain
  → {
      gene: "ABL1",
      function: "Non-receptor tyrosine-protein kinase...",
      go_terms: [{id: "GO:0004672", term: "F:protein kinase activity"}, ...],
      sequence_length: 1130,
      binding_sites: [{type: "Binding site", position: "315-315"}, ...],
      domains: [{name: "SH3 domain", range: "83-142"}, ...]
    }
```

---

### PubChem
**Connector:** `connectors/pubchem.py`  
**API:** PubChem PUG REST  
**Base URL:** `https://pubchem.ncbi.nlm.nih.gov/rest/pug`  
**Auth:** None (keyless)  
**What we fetch:** Canonical SMILES, molecular formula, molecular weight, IUPAC name  
**Used by:** Medicinal Chemist (scaffold chemistry)

```
GET /compound/cid/5291/property/SMILES,MolecularFormula,MolecularWeight,IUPACName/JSON
  → {
      cid: "5291",
      canonical_smiles: "CC1=C(C=C...)...",
      molecular_formula: "C29H31N7O",
      molecular_weight: "493.6",
      iupac_name: "4-[(4-methylpiperazin-1-yl)methyl]-N-..."
    }
```

---

### ClinVar
**Connector:** `connectors/clinvar.py`  
**API:** NCBI E-utilities (ClinVar database)  
**Base URL:** `https://eutils.ncbi.nlm.nih.gov/entrez/eutils`  
**Auth:** Optional NCBI key  
**What we fetch:** Gene variants, clinical significance, associated conditions  
**Used by:** Pathologist exclusively

```
GET /esearch.fcgi?db=clinvar&term=ABL1[gene]+AND+imatinib+resistance+OR+pathogenic
  → List of variant IDs

GET /esummary.fcgi?db=clinvar&id=<ids>
  → [{title: "NM_005157.6(ABL1):c.944C>T (p.Thr315Ile)",
      clinical_significance: "Pathogenic",
      condition: "Chronic myelogenous leukemia"}, ...]
```

---

### Reactome
**Connector:** `connectors/reactome.py`  
**API:** Reactome ContentService REST  
**Base URL:** `https://reactome.org/ContentService`  
**Auth:** None  
**What we fetch:** Biological pathways the target protein participates in  
**Used by:** Cell / Molecular Biologist exclusively

```
GET /data/mapping/UniProt/P00519/pathways
  → [{stId: "R-HSA-9704933",
      displayName: "Signaling by BCR-ABL1 oncoproteins",
      speciesName: "Homo sapiens"}, ...]

GET /search/query?query=BCR-ABL+signaling&types=Pathway
  → Full-text search results for pathways
```

---

### AlphaFold DB
**Connector:** `connectors/alphafold.py`  
**API:** EMBL-EBI AlphaFold REST API  
**Base URL:** `https://alphafold.ebi.ac.uk/api`  
**Auth:** None  
**What we fetch:** AI-predicted structure metadata — entry ID, model URL, pLDDT confidence score, sequence length  
**Used by:** Computational Biologist exclusively

```
GET /prediction/P00519
  → [{
      entryId: "AF-P00519-F1",
      pdbUrl: "https://alphafold.ebi.ac.uk/files/AF-P00519-F1-model_v4.pdb",
      globalMetricValue: 87.3,   ← pLDDT confidence (0-100)
      seqLength: 1130,
      organismScientificName: "Homo sapiens"
    }]
```

---

## 6. Streaming Architecture (SSE)

Facet uses **Server-Sent Events (SSE)** to push Claude's tokens to the browser in real time. All 4 personas stream concurrently — the browser receives an interleaved stream of events tagged by `persona`.

### Event Format

Every event sent over the SSE stream is a JSON object:

```json
// Status updates (pipeline stage changes)
{"type": "status", "stage": "parsing",   "message": "Extracting entity and target…"}
{"type": "status", "stage": "resolved",  "message": "ChEMBL: CHEMBL941 · UniProt: P00519"}
{"type": "status", "stage": "retrieved", "message": "Data gathered — synthesising responses…"}

// Token events (Claude streaming — one per token)
{"type": "token", "persona": "medicinal_chemist", "text": "## SAR"}
{"type": "token", "persona": "medicinal_chemist", "text": " Summary"}
{"type": "token", "persona": "pathologist",       "text": "## Resistance"}

// Done event (pipeline complete)
{"type": "done", "metadata": {
  "entity": "imatinib",
  "target": "ABL1",
  "personas_run": ["medicinal_chemist", "pathologist", "cell_biologist", "comp_biologist"],
  "databases_queried": ["chembl", "clinvar", "pdb", "pubchem", "pubmed", "reactome", "uniprot", "alphafold"],
  "llm_calls": 5
}}
```

### Concurrent Streaming Flow

```
orchestrator.py                  Claude API (4 concurrent streams)
     │
     ├─── asyncio.create_task(stream_one_persona("medicinal_chemist"))  ──►  Sonnet 4.6
     ├─── asyncio.create_task(stream_one_persona("pathologist"))         ──►  Sonnet 4.6
     ├─── asyncio.create_task(stream_one_persona("cell_biologist"))      ──►  Sonnet 4.6
     └─── asyncio.create_task(stream_one_persona("comp_biologist"))      ──►  Sonnet 4.6
                    │
                    │  tokens arrive concurrently → shared asyncio.Queue
                    ▼
             token_queue.get()
                    │
                    ▼
        FastAPI SSE endpoint
                    │
                    ▼
           Browser (index.html)
        JS routes each token to
        the correct panel by persona
```

### Browser-Side SSE Client

```javascript
// index.html — the JS SSE listener
const response = await fetch('/api/query', {method: 'POST', body: JSON.stringify(body)});
const reader = response.body.getReader();

while (true) {
  const {done, value} = await reader.read();
  if (done) break;

  // Parse "data: {...}\n" lines
  const event = JSON.parse(line.slice(6));

  if (event.type === 'token') {
    // Route token to the correct panel
    rawTokens[event.persona] += event.text;
    panel.innerHTML = marked.parse(rawTokens[event.persona]);  // live markdown render
  }
}
```

---

## 7. User Identity & Persona Detection

Facet uses a **two-layer approach** to know who the user is. No passwords, no database — just session storage and AI inference.

### Layer 1 — Profile Card Selection (Primary)

The landing page presents 4 role cards. The user clicks their role. It is stored in `sessionStorage`:

```javascript
sessionStorage.setItem('persona', 'medicinal_chemist');
```

This persists for the browser session. The query screen shows their role in the header and routes all responses through that lens.

### Layer 2 — LLM Auto-Detection (Fallback)

If the user skips role selection, Facet analyses their query language with a lightweight Claude Haiku call:

```
File: entity_resolver.py::detect_persona()
Model: claude-haiku-4-5 (fast + cheap — 1 call)

Input:  "I want to check IC50 and SAR data for imatinib analogues against ABL1"

System: "Classify this query by professional role:
         medicinal_chemist: asks about IC50, SAR, scaffolds, co-crystals
         pathologist: asks about mutations, resistance, clinical significance
         cell_biologist: asks about pathways, signaling, mechanism
         comp_biologist: asks about structures, sequences, docking, datasets"

Output: { "persona_id": "medicinal_chemist", "confidence": 0.95 }
```

If confidence > 0.6, a banner appears: *"Detected: 🧪 Medicinal Chemist [That's me ✓] [Change]"*

### Detection Accuracy (from test results)

All 4 persona detection tests pass with 100% accuracy on domain-specific queries:

| Query Type | Detected As | Confidence |
|---|---|---|
| SAR / IC50 / scaffold language | medicinal_chemist | > 0.90 |
| T315I / mutation / clinical patient | pathologist | > 0.90 |
| BCR-ABL / STAT5 / signaling / phosphorylation | cell_biologist | > 0.85 |
| PDB / AlphaFold / pLDDT / docking | comp_biologist | > 0.90 |

---

## 8. Caching Strategy

Facet has two levels of caching:

### Level 1 — Query Parse Cache
**Location:** `cache/parse_<md5>.json`  
**What:** Result of Step 1 (LLM entity extraction)  
**Key:** MD5 hash of the raw query string  
**Why:** Avoids re-calling Claude for the same question phrased identically

### Level 2 — Full Pipeline Demo Cache
**Location:** `cache/<entity>_<target>.json`  
**What:** All 8 connector responses for all 4 personas  
**Key:** `{entity}_{target}` (e.g. `imatinib_abl1.json`)  
**Why:** The "Demo" button loads this instantly — no live API calls on stage

**Cache structure:**
```json
{
  "ids": {
    "entity": "imatinib",
    "target": "ABL1",
    "drug_pubchem": "5291",
    "drug_chembl": "CHEMBL941",
    "target_uniprot": "P00519",
    "target_chembl": "CHEMBL1862"
  },
  "evidence": {
    "medicinal_chemist": {
      "chembl":  { "activities": [...], "count": 100 },
      "pdb":     { "structures": [...] },
      "pubchem": { "cid": "5291", "canonical_smiles": "..." },
      "pubmed":  { "abstracts": [...] }
    },
    "pathologist": {
      "clinvar": { "variants": [...] },
      "pubmed":  { "abstracts": [...] }
    },
    ...
  }
}
```

**To pre-populate the demo cache before presenting:**
```bash
uv run python3 -c "
import asyncio
from dotenv import load_dotenv
load_dotenv()
from orchestrator import run_pipeline
asyncio.run(run_pipeline('What do I need to know about imatinib and its target ABL1?'))
print('Cache ready!')
"
```

---

## 9. File & Module Reference

```
Facet/
│
├── main.py                     FastAPI app — HTTP routes + SSE endpoint
│                               Routes: GET /, GET /api/health,
│                                       GET /api/personas, POST /api/detect-persona,
│                                       POST /api/query (SSE stream)
│
├── orchestrator.py             5-step pipeline coordinator
│                               Functions: get_persona_plan(), retrieve_for_persona(),
│                                          synthesize_stream(), stream_pipeline(),
│                                          run_pipeline()
│
├── entity_resolver.py          Steps 1+2 + persona detection
│                               Functions: parse_query(), resolve_ids(), detect_persona()
│
├── connectors/
│   ├── __init__.py             REGISTRY dict mapping name → fetch function
│   ├── pubmed.py               NCBI E-utilities → paper abstracts
│   ├── chembl.py               EBI ChEMBL → activity data + datasets
│   ├── pdb.py                  RCSB PDB → 3D structure entries
│   ├── uniprot.py              UniProt → protein function + sequence
│   ├── pubchem.py              PubChem → SMILES + molecular properties
│   ├── clinvar.py              NCBI ClinVar → gene variants
│   ├── reactome.py             Reactome → biological pathways
│   └── alphafold.py            EMBL-EBI AlphaFold → predicted structures
│
├── personas/
│   ├── medicinal_chemist.yaml  Chemist lens config
│   ├── pathologist.yaml        Pathologist lens config
│   ├── cell_biologist.yaml     Cell biologist lens config
│   └── comp_biologist.yaml     Computational biologist lens config
│
├── frontend/
│   └── index.html              Single-page app
│                               • Landing page (role cards)
│                               • Single-persona query view
│                               • 4-panel compare view
│                               • SSE client (vanilla JS)
│                               • TailwindCSS CDN (no build step)
│                               • marked.js for live markdown rendering
│
├── cache/
│   └── *.json                  Pre-fetched pipeline results (demo safety net)
│
├── tests/
│   ├── conftest.py             Shared fixtures + DEMO_IDS + PERSONA_QUERIES
│   ├── test_connectors.py      12 tests — each connector vs live APIs
│   ├── test_entity_resolver.py 10 tests — LLM parse + ID resolve + detect
│   ├── test_api.py             FastAPI endpoint tests (health, personas, SSE)
│   └── e2e/
│       ├── conftest.py         Playwright viewport + recording config
│       ├── test_ui.py          9 navigation/UI tests (no LLM calls, fast)
│       └── test_full_personas.py  18 full E2E tests with video recording
│                                  4 personas × 3 questions + 2 compare + 4 auto-detect
│
├── pyproject.toml              uv project config + dependencies
├── uv.lock                     Exact dependency versions (commit this)
├── .env.example                Template for API keys
├── .env                        Your actual keys (gitignored)
└── .gitignore                  Excludes .env and .venv
```

---

## 10. Data Flow Diagrams

### Single Persona Query Flow

```
User types query
       │
       ▼
POST /api/query  { query, persona: "medicinal_chemist" }
       │
       ▼
[Step 1] parse_query()  ──► Claude Haiku (1 LLM call, cached)
       │
       │  { entity: "imatinib", target: "ABL1" }
       ▼
[Step 2] resolve_ids()  ──► PubChem + ChEMBL + UniProt + ChEMBL (parallel HTTP)
       │
       │  { drug_pubchem: "5291", drug_chembl: "CHEMBL941", ... }
       ▼
[Step 3] get_persona_plan()  ──► Read personas/medicinal_chemist.yaml
       │
       │  [ {chembl, activity}, {pdb, ligand_search}, {pubchem, scaffold}, {pubmed, SAR} ]
       ▼
[Step 4] retrieve_for_persona()  ──► ChEMBL + PDB + PubChem + PubMed (parallel HTTP)
       │
       │  { chembl: {activities:[...]}, pdb: {structures:[...]}, ... }
       ▼
[Step 5] synthesize_stream()  ──► Claude Sonnet 4.6 (streaming)
       │
       │  tokens streamed via SSE
       ▼
Browser panel renders markdown in real time
```

### 4-Panel Compare Mode Flow

```
User submits query (no persona selected)
       │
       ▼
[Steps 1+2]  parse + resolve  (once, shared)
       │
       ▼
[Step 3] load ALL 4 persona plans
       │
       ▼
[Step 4] retrieve for all 4 personas concurrently
         (up to 8 databases queried in parallel)
       │
       ▼
[Step 5] synthesize all 4 personas concurrently
         ├── stream_one_persona("medicinal_chemist") ──► Sonnet 4.6
         ├── stream_one_persona("pathologist")        ──► Sonnet 4.6
         ├── stream_one_persona("cell_biologist")     ──► Sonnet 4.6
         └── stream_one_persona("comp_biologist")     ──► Sonnet 4.6
                    │
                    ▼ interleaved SSE token events
Browser routes each token to the correct panel column
All 4 panels write simultaneously
```

---

## 11. LLM Call Budget

| Call | Model | When | Tokens (approx.) |
|---|---|---|---|
| Entity parse | Claude Haiku 4.5 | Step 1 — once per unique query | ~200 in / 50 out |
| Persona detect | Claude Haiku 4.5 | Optional — if no role selected | ~300 in / 30 out |
| Synthesis × 4 | Claude Sonnet 4.6 | Step 5 — one per persona | ~2,000 in / 800 out each |

**Total per full compare-mode query:**
- ~5 LLM calls
- ~9,000 input tokens + ~3,200 output tokens
- **Cost:** ~$0.07 per full run at current Sonnet 4.6 pricing

**With $200 API credit budget:** ~2,800 full runs before exhausting budget.

---

## 12. Tech Stack Summary

| Layer | Technology | Why |
|---|---|---|
| Backend | Python 3.11 + FastAPI | Async support for concurrent API calls + SSE streaming |
| HTTP client | httpx (async) | All 8 biomedical connectors run in parallel with `asyncio.gather()` |
| LLM | Anthropic Claude API | Haiku for speed (parse/detect) · Sonnet for quality (synthesis) |
| Streaming | Server-Sent Events (SSE) via `sse-starlette` | Push tokens to browser without WebSocket complexity |
| Frontend | HTML + TailwindCSS CDN + Vanilla JS | Zero build step, polished product UI, runs from a single file |
| Markdown | marked.js (CDN) | Live markdown rendering as Claude streams tokens |
| Config | YAML (`pyyaml`) | Persona definitions editable by SME without touching Python |
| Package manager | uv | Fast installs, lockfile (`uv.lock`) for reproducible environments |
| Testing — backend | pytest + pytest-asyncio | Async connector and API tests |
| Testing — E2E | Playwright + pytest-playwright | Full browser automation with video recording |

---

## 13. Running the System

### Prerequisites

```bash
# 1. Install uv (if not installed)
brew install uv

# 2. Clone and install
git clone git@github.com:drkeerthiharikrishnan-h/Facet.git
cd Facet
uv sync

# 3. Configure API keys
cp .env.example .env
# Edit .env:
#   ANTHROPIC_API_KEY=<your Anthropic API key>
#   NCBI_API_KEY=<your free NCBI key from ncbi.nlm.nih.gov/account>

# 4. Start the server
uv run uvicorn main:app --reload --port 8000

# 5. Open the app
open http://localhost:8000
```

### Running Tests

```bash
# Backend connector tests (real APIs, no LLM)
uv run pytest tests/test_connectors.py -v

# Entity resolver tests (LLM calls — uses API credits)
uv run pytest tests/test_entity_resolver.py -v

# Fast UI navigation tests (no LLM)
uv run pytest tests/e2e/test_ui.py -v --base-url=http://localhost:8000 \
  -k "landing or clicking or compare_all or demo_button"

# Full E2E with video recording (all 4 personas, 3 questions each)
uv run pytest tests/e2e/test_full_personas.py -v \
  --headed --video=on --output=test-recordings --slowmo=600 \
  --base-url=http://localhost:8000
```

### Pre-loading Demo Cache (run before presenting)

```bash
uv run python3 -c "
import asyncio
from dotenv import load_dotenv; load_dotenv()
from orchestrator import run_pipeline
result = asyncio.run(run_pipeline(
    'What do I need to know about imatinib and its target ABL1?'
))
print(f'Cache saved: entity={result[\"entity\"]} target={result[\"target\"]}')
"
```

Then click the **Demo** button in the UI for instant, zero-latency demo responses.

---

*Facet v1.0 — Built at the Gladstone Institute × Cerebral Valley Hackathon, July 2026*
