# Persona × Connector × Formatter — Drug/Target Dossier Pipeline

Generate discipline-specific reference dossiers for **any drug/target query** by
(1) auto-resolving identifiers from a plain name, (2) pulling live data from a bank
of bioinformatics connectors, and (3) synthesizing a persona-styled document.
Erlotinib/EGFR is the worked example; nothing about it is hardcoded.

```
drug name (+optional target)
        │
        ▼
   resolver.py ──────────► entity_ids.json   (ChEMBL / PubChem / UniProt / Ensembl /
        │                                      PDB id / ligand code / numbering offset)
        ▼
   orchestrator.py ─── runs each persona's connector list ──► connector_payload_<persona>.json
        │
        ▼
   persona YAML  +  response_formatter.txt  +  payload
        │
        ▼            (LLM synthesis)
   generated_<persona>.md      ← the dossier
```

## Layout

| File / dir | Role |
|---|---|
| `resolver.py` | From a drug name (+optional target) resolves ALL identifiers: drug/target ChEMBL, PubChem CID, UniProt, Ensembl, best co-crystal PDB, bound-ligand code, and the legacy→UniProt residue-numbering offset. Target is inferred from ChEMBL mechanism when not given. |
| `orchestrator.py` | Runner. `run_from_names(persona_yaml, drug, target=None, ...)` does resolve → connectors → synthesis-prompt. `run_persona(persona_yaml, entity_ids, ...)` runs from an already-resolved manifest. Threads the primary-target potency from ChEMBL into ligand-efficiency. |
| `connectors/` | 17 data connectors (see below). Each returns a plain dict; structural/potency params fall back from persona `params` → `entity_ids`, so no per-persona hardcoding. |
| `*.yaml` (4) | Persona definitions — `cell_biologist.yaml` (molecular biologist), `pathologist.yaml`, `comp_biologist.yaml`, `medicinal_chemist.yaml`. Each holds the connector list, reasoning rules, and a DOSSIER MODE section skeleton (erlotinib demoted to a labeled example). |
| `response_formatter.txt` | Shared response template / voice + fidelity rules consumed at synthesis. |
| 
### Connectors (`connectors/`)
`pubchem` (identity/SMILES from name), `chembl` (targets + selectivity/potency),
`rdkit_descriptors` (MW, cLogP, TPSA, QED, Fsp3, ESOL, ligand efficiency),
`pdb` (best co-crystal + contact geometry), `admet`, `opentargets`, `uniprot`,
`proteinatlas`, `clinvar`, `pubmed`, `alphafold`, `string_ppi`, `gtex`,
`interpro`, `reactome`, plus `utils.py`.

## Running it

```python
import orchestrator
# fully from names — resolves everything, runs connectors, builds the prompt:
out = orchestrator.run_from_names("cell_biologist.yaml", "erlotinib", target="EGFR")
prompt = out["synthesis_prompt"]          # feed to your LLM
# … dossier = llm(prompt)

# any drug works, target optional (inferred from ChEMBL mechanism):
out = orchestrator.run_from_names("comp_biologist.yaml", "imatinib")
out = orchestrator.run_from_names("medicinal_chemist.yaml", "vemurafenib")
```

Synthesis itself is done by whatever LLM you wire in; in Claude Science this was
`host.llm(prompt, model=host.reasoning_model())`.

## Design rules (why it generalizes)

- **No drug facts in the YAMLs.** Persona files hold only the connector list,
  discipline reasoning rules, and a generic section skeleton. Erlotinib appears
  only as a labeled "WORKED EXAMPLE — not to be emitted unless the compound IS
  erlotinib."
- **Connectors read `params` then fall back to `entity_ids`.** Structural
  (`ligand_code`, `numbering_offset`) and potency (`pIC50_values`, `comparators`)
  inputs thread from the resolver, not from hardcoded persona params.
- **Retrieved values are sacrosanct.** Connector/RDKit values must appear verbatim
  in the dossier; enrichment (established pharmacology) is allowed but must be
  labeled and must never contradict or fabricate retrieved data.
- **Graceful degradation.** Missing resolver fields (e.g. no co-crystal) are
  handled by the connectors rather than crashing.

