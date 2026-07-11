# Facet — Four Personas, One Query (Developer Guide)

**Audience: developers, no biology background needed.** This explains the domain in plain English, then shows how the *same* question produces four different answers depending on the user's role. Scope is **MVP, not production**: open databases only, no heavy middleware, and LLM calls bundled to the minimum.

Companion: `facet-e2e-worked-example-medicinal-chemist.md` has the full code for one persona. This doc is the wider map across all four.

---

# Part A — Context for non-scientists (read once)

## A1. The problem in one paragraph

A scientist searches for a drug (say **imatinib**, a cancer drug) or a gene. Generic search gives everyone the same averaged answer. But a chemist, a pathologist, a cell biologist, and a computational biologist each need *different evidence* about the same thing. Facet makes the user's **role** (the "persona") change **which databases we query, what we pull out, and how we structure the answer** — not just the wording.

## A2. Plain-English glossary

You don't need to learn biology. Here's just enough to read the rest.

| Term | Plain English |
|---|---|
| **Drug / compound** | A molecule designed to affect the body. `imatinib` is our example. |
| **Target** | The protein the drug acts on. Imatinib's main target is a protein called **ABL1**. |
| **Gene vs protein** | A gene is the "code"; the protein is the "machine" built from it. `ABL1` is both a gene name and (as a protein) a target. |
| **Kinase** | A common *type* of protein/target that acts like a molecular on-switch. ABL1 is a kinase. |
| **Binding affinity (IC50/Ki)** | A *number* for how strongly a drug grabs its target. Lower = stronger. Think "score". |
| **SAR** (structure–activity relationship) | "If I change this part of the molecule, does it get stronger or weaker?" The chemist's core question. |
| **Structure / co-crystal** | A 3D model of the protein, sometimes with the drug sitting inside it — like a CAD file. |
| **Mutation / variant** | A change in the gene. Some mutations make a drug **stop working** (resistance). |
| **Pathway / signaling** | The "wiring diagram" of which proteins tell which other proteins what to do. |
| **Sequence** | The protein's raw string of amino-acid letters — the input to modeling. |

## A3. The databases in plain English

Every source below is **open** and has either a **REST API** (you `GET` a URL, you get JSON back) or a **downloadable dump** you can host locally. No logins except a free rate-limit key for NCBI.

| Database | What it is (plain English) | Open? | Access |
|---|---|---|---|
| **PubMed** | "Google Scholar for biomedical papers." You get titles + abstracts. | Yes | REST (NCBI E-utilities), free key |
| **ChEMBL** | "This molecule was tested on this protein; here's the strength number." | Yes | REST + full DB download |
| **PDB** (RCSB) | 3D experimental structures of proteins (± the drug inside). | Yes | REST/GraphQL + file download |
| **UniProt** | "Wikipedia for proteins": what it does + its sequence. | Yes | REST + download |
| **PubChem** | Chemical info for compounds (IDs, the molecule's shape/scaffold). | Yes | REST |
| **ClinVar** | Catalog of gene variants and whether they matter clinically (e.g. cause resistance). | Yes | REST (NCBI) + VCF download |
| **Reactome** | Curated "wiring diagrams" — pathways and signaling. | Yes | REST (ContentService) + download |
| **AlphaFold DB** | AI-**predicted** 3D structures for proteins that lack an experimental one. | Yes | REST + FTP download |

Avoid **KEGG** and **COSMIC** — similar data but licensing friction. Reactome + ClinVar cover the same ground for free.

## A4. What a "persona" is

The persona is the **user's job role**, chosen from a dropdown in the UI. It is **not** guessed from their question. Each persona is just a small config file (YAML) that says: *for this role, hit these databases, pull these fields, and structure the answer with these sections.* Adding a role later = adding one file, no code change.

## A5. How the pipeline works (and the MVP shortcuts)

Five steps. Only the last touches an LLM per persona:

1. **Understand** the question → pull out the entity ("imatinib") + a focus. *(1 shared LLM call, or a name-matcher. Cached.)*
2. **Resolve** the entity → its IDs and target (ABL1). *(Plain HTTP, cached.)*
3. **Plan** from the persona's YAML → which databases + keywords. *(Config lookup, no LLM.)*
4. **Retrieve** → call those databases' APIs (HTTP). Structured results (numbers, IDs) are mapped to a common shape **with no LLM**. Papers are kept as raw abstracts.
5. **Synthesize** → **one bundled LLM call per persona** that takes the structured findings + a few raw abstracts and writes the sectioned, cited answer.

**MVP shortcuts (deliberate):**
- **Bundle the LLM calls.** Don't run one call per paper. For each persona, a *single* call does light extraction **and** writing together. Total for the 4-panel demo = **1 parse call + 4 synthesis calls = 5 LLM calls.**
- **No reranker, no vector DB.** Take PubMed's top ~5 by relevance and feed them straight in. (A reranker is an optional later upgrade.)
- **Deterministic where possible.** Numbers/IDs from ChEMBL/PDB/UniProt/ClinVar become evidence by plain field-mapping — the model never parses them.
- **No middleware.** Just `requests` (HTTP) + one `anthropic` call. No orchestration framework, no services.

---

# Part B — The query

## B1. The shared query (top — used for the 4-panel demo)

> **"What do I need to know about imatinib and its target ABL1?"**

This neutral question goes to **all four** personas so the side-by-side difference is caused only by the lens, not by different words.

## B2. What each user would really ask (their natural questions)

In real single-user use, each role phrases it their own way. The entity resolved is identical (`imatinib` → ABL1); the persona toggle picks the lens.

| Persona | The question they'd actually type |
|---|---|
| **Medicinal chemist** | *"I'm optimizing imatinib analogues against ABL1 — what's the SAR, and are there co-crystal structures of the ABL1 complex I can use?"* |
| **Pathologist** | *"This CML patient stopped responding to imatinib — is there an ABL1 mutation that explains resistance, and what's its clinical significance?"* |
| **Cell / molecular biologist** | *"How does imatinib blocking ABL1 change downstream signaling — which pathways and partner proteins are involved?"* |
| **Computational biologist** | *"I need structural and sequence inputs to model imatinib–ABL1 binding — what experimental/predicted structures, sequences, and bioactivity datasets exist?"* |

---

# Part C — Per-persona flow

Each section: who they are · their databases · the actual tool calls · keywords · what we extract · answer sections. All identifiers are real: `imatinib` = ChEMBL `CHEMBL941`, PubChem CID `5291`; `ABL1` = UniProt `P00519`, ChEMBL target `CHEMBL1862`; PDB `1IEP` = ABL1 + imatinib.

## C1. Medicinal chemist

**Who they are:** designs and tweaks the drug molecule. Wants potency numbers, the 3D fit, and how changing the molecule changes potency.

**Databases:** ChEMBL (potency), PDB (structures), PubChem (scaffold), PubMed (SAR papers).

**Tool calls:**
```
GET  https://www.ebi.ac.uk/chembl/api/data/activity.json
       ?molecule_chembl_id=CHEMBL941&target_chembl_id=CHEMBL1862&standard_type__in=IC50,Ki,Kd
POST https://search.rcsb.org/rcsbsearch/v2/query        # find structures with ligand "STI" (imatinib)
GET  https://data.rcsb.org/rest/v1/core/entry/1IEP      # title, resolution
GET  https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/5291/property/CanonicalSMILES/JSON
GET  https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=imatinib+SAR
```
**Keywords / expansion:** `structure-activity relationship`, `co-crystal`, `IC50`, `scaffold`, `analogue`.
**Extract (fields):** `binding_affinity`, `structures`, `scaffold`, `sar_notes`.
**Answer sections:** SAR summary · Key structures · Bioactivity · Open questions.
**Why different:** only persona pulling potency numbers + 3D structures + scaffold chemistry.

## C2. Pathologist

**Who they are:** interprets a patient's disease/genetics. Wants to know which mutation explains resistance and what it means clinically.

**Databases:** ClinVar (variants + clinical significance), PubMed (resistance/diagnostic literature).

**Tool calls:**
```
GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi
      ?db=clinvar&term=ABL1[gene]+AND+imatinib+resistance&retmode=json
GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=clinvar&id=<ids>&retmode=json
GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi
      ?db=pubmed&term=imatinib+resistance+ABL1+T315I
```
**Keywords / expansion:** `resistance mutation`, `T315I`, `clinical significance`, `prognosis`, `diagnostic`.
**Extract (fields):** `resistance_variants`, `diagnostic_correlates`, `therapy_context`.
**Answer sections:** Resistance landscape · Diagnostic correlates · Clinical notes · Open questions.
**Why different:** only persona hitting ClinVar; cares about *mutations and patients*, not potency or wiring.

## C3. Cell / molecular biologist

**Who they are:** studies how the drug/target works inside cells — pathways, signaling, mechanism.

**Databases:** Reactome (pathways), UniProt (protein function), PubMed (mechanism/signaling). *(Optional: STRING for interaction partners.)*

**Tool calls:**
```
GET https://reactome.org/ContentService/data/mapping/UniProt/P00519/pathways   # pathways ABL1 is in
GET https://reactome.org/ContentService/search/query?query=BCR-ABL+signaling
GET https://rest.uniprot.org/uniprotkb/P00519.json?fields=cc_function,go       # function + GO terms
GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi
      ?db=pubmed&term=BCR-ABL+signaling+downstream+STAT5
# optional partners:
GET https://string-db.org/api/json/interaction_partners?identifiers=ABL1&species=9606
```
**Keywords / expansion:** `signaling pathway`, `mechanism of action`, `downstream`, `BCR-ABL`, `phosphorylation`.
**Extract (fields):** `pathways`, `function`, `mechanism`, `interactions`.
**Answer sections:** Pathway context · Mechanism of action · Key interactions · Open questions.
**Why different:** only persona pulling pathways/interactions; cares about the *biological wiring*, not molecule design.

## C4. Computational biologist

**Who they are:** builds models/simulations. Needs machine-readable structures, sequences, and datasets.

**Databases:** PDB (experimental structures), AlphaFold DB (predicted structures), UniProt (sequence + features), ChEMBL (bioactivity dataset for ML). PubMed (methods).

**Tool calls:**
```
POST https://search.rcsb.org/rcsbsearch/v2/query                      # all imatinib–ABL1 entries
GET  https://data.rcsb.org/rest/v1/core/entry/1IEP                    # resolution, method, ligand
GET  https://alphafold.ebi.ac.uk/api/prediction/P00519               # predicted model + pLDDT confidence
GET  https://rest.uniprot.org/uniprotkb/P00519.json?fields=sequence,ft_binding,ft_domain
GET  https://www.ebi.ac.uk/chembl/api/data/activity.json?target_chembl_id=CHEMBL1862&limit=1000
```
**Keywords / expansion:** `crystal structure`, `binding site`, `molecular docking`, `dataset`, `sequence`, `pLDDT`.
**Extract (fields):** `structures`, `predicted_structure`, `sequence_features`, `datasets`.
**Answer sections:** Available structures · Sequence & site · Datasets · Open questions.
**Why different:** only persona that wants *both* experimental and AI-predicted structures + a bulk activity dataset for modeling.

**One entity, four routings — near-zero overlap:**

| | chemist | pathologist | cell/mol biol | comp biol |
|---|:--:|:--:|:--:|:--:|
| ChEMBL | ✅ (potency) | | | ✅ (dataset) |
| PDB | ✅ | | | ✅ |
| PubChem | ✅ | | | |
| ClinVar | | ✅ | | |
| Reactome | | | ✅ | |
| UniProt | | | ✅ | ✅ |
| AlphaFold | | | | ✅ |
| PubMed | ✅ | ✅ | ✅ | ✅ |

PubMed is shared (everyone reads papers) — but with **different keywords**, so even the abstracts pulled differ.

---

# Part D — Side-by-side: four synthesized panels

Same input — *"What do I need to know about imatinib and its target ABL1?"* — four lenses. Note how the databases, the numbers, and the section headings all change. `[E#]` markers link to the real records each panel retrieved.

```
┌──────────────────────────────────────┬──────────────────────────────────────┐
│ 🧪 MEDICINAL CHEMIST                  │ 🔬 PATHOLOGIST                        │
│ sources: ChEMBL · PDB · PubChem · PMed│ sources: ClinVar · PubMed             │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ SAR summary                          │ Resistance landscape                  │
│ 2-phenylaminopyrimidine core; the    │ The ABL1 T315I "gatekeeper" mutation  │
│ N-methylpiperazine tail aids         │ abolishes imatinib binding and is the │
│ solubility & potency [E3].           │ classic resistance driver [E1].       │
│                                      │                                       │
│ Key structures                       │ Diagnostic correlates                 │
│ PDB 1IEP: ABL1 kinase + imatinib,    │ BCR-ABL transcript (Ph chromosome)    │
│ 2.1 Å, DFG-out inactive form [E1].   │ defines CML; monitor for KD mutations │
│                                      │ on relapse [E2].                      │
│ Bioactivity                          │ Clinical notes                        │
│ IC50 ≈ 0.1 µM vs ABL1 [E2].          │ T315I → switch to ponatinib; most     │
│                                      │ other KD mutants keep partial         │
│ Open questions                       │ sensitivity [E3].                     │
│ No KIT/PDGFRA structures in set.     │ Open questions                        │
│                                      │ Variant-specific dosing not covered.  │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ 🧬 CELL / MOLECULAR BIOLOGIST        │ 💻 COMPUTATIONAL BIOLOGIST            │
│ sources: Reactome · UniProt · PubMed  │ sources: PDB · AlphaFold · UniProt ·  │
│                                      │          ChEMBL                       │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ Pathway context                      │ Available structures                  │
│ ABL1 sits in "Signaling by BCR-ABL"; │ Experimental: PDB 1IEP (2.1 Å,        │
│ constitutive kinase drives           │ imatinib-bound, DFG-out) + 2HYY,      │
│ proliferation [E1].                  │ 6HD6 [E1].                            │
│                                      │ Predicted: AlphaFold AF-P00519-F1     │
│ Mechanism of action                  │ (full-length, pLDDT-scored) [E2].     │
│ Imatinib locks the inactive          │                                       │
│ conformation, halting downstream     │ Sequence & site                       │
│ phosphorylation (CrkL, STAT5) [E2].  │ UniProt P00519; ATP-site binding      │
│                                      │ residues incl. gatekeeper T315 [E3].  │
│ Key interactions                     │                                       │
│ Feeds RAS/MAPK, PI3K/AKT, STAT5      │ Datasets                              │
│ signaling [E3].                      │ ChEMBL: ~N bioactivities vs ABL1 for  │
│                                      │ model training [E4].                  │
│ Open questions                       │ Open questions                        │
│ Cell-type specificity not covered.   │ No MD trajectories in public sources. │
└──────────────────────────────────────┴──────────────────────────────────────┘
```

Read across: the chemist gets **numbers + 3D fit**, the pathologist gets **a mutation + what to do about it**, the cell biologist gets **the wiring**, the computational biologist gets **files + a dataset**. Same drug. That contrast *is* the product.

---

# Part E — MVP build notes

**Bundled LLM calls.** Per persona, one call does extraction + synthesis together:
```python
# one call per persona — no per-paper calls, no reranker
system = persona_sections + "Cite only [E#] from the evidence; omit unsupported claims."
user   = { "question": q,
           "structured_evidence": mapped_records,   # ChEMBL/PDB/etc., already field-mapped (no LLM)
           "abstracts": top5_pubmed_raw }            # model reads these directly
answer = client.messages.create(model="claude-sonnet-5", max_tokens=1200,
                                system=system, messages=[{"role":"user","content":json.dumps(user)}])
```
Demo total: **1 parse + 4 synthesis = 5 calls.** At a few thousand tokens each, the $200 credit covers hundreds of full runs.

**Open-data only, with local-copy option.** Every source in this doc is open and downloadable, so if an API rate-limits during the demo you can pre-download and serve locally:
- ChEMBL: full DB dump (SQLite/Postgres). · PDB: per-entry mmCIF files. · UniProt: FASTA + JSON. · ClinVar: VCF. · Reactome: BioPAX/SBML. · AlphaFold: FTP proteome files. · PubMed: pre-fetch the demo abstracts and cache them.
- **MVP tip:** pre-fetch and cache the `imatinib`/`ABL1` responses for all four personas before demoing. Never call live APIs cold on stage.

**No middleware.** The whole thing is: a dict of persona YAMLs, a folder of small connector functions (`requests` in, common evidence dict out), and one `anthropic` call. No queue, no orchestrator, no vector store. If you outgrow it later, the persona YAMLs and connectors lift straight into a bigger host unchanged.

**Free keys needed:** NCBI E-utilities key (PubMed/ClinVar) and your Anthropic API key. Everything else is keyless.
