```
ERLOTINIB - MOLECULAR BIOLOGY / MECHANISM PROFILE
Reversible, ATP-competitive 4-anilinoquinazoline inhibitor of the EGFR tyrosine kinase domain
Source: ChEMBL CHEMBL553 (erlotinib) vs CHEMBL203 (EGFR, UniProt P00533) + established ErbB/RTK cell biology
```

## 1. IDENTITY & CONSTITUTION
PubChem CID 176870. Molecular formula C22H23N3O4, molecular weight 393.4. IUPAC name: N-(3-ethynylphenyl)-6,7-bis(2-methoxyethoxy)quinazolin-4-amine. Canonical SMILES: `COCCOC1=C(C=C2C(=C1)C(=NC=N2)NC3=CC=CC(=C3)C#C)OCCOC`. Scaffold class: 4-anilinoquinazoline kinase-inhibitor chemotype — a quinazoline core bearing a 3-ethynylaniline at C4 (the hinge-binding/selectivity vector) and two 2-methoxyethoxy solubilizing groups at C6/C7.

## 2. MOLECULAR MECHANISM
Erlotinib occupies the ATP-binding cleft of the EGFR intracellular tyrosine kinase domain, competing directly with ATP — the interaction is structurally documented in PDB 1M17 ("EGFR tyrosine kinase domain with 4-anilinoquinazoline inhibitor erlotinib," 2.6 Å, X-ray diffraction). The kinase domain corresponds to InterPro IPR000719 (Protein kinase domain), IPR001245 (Ser/Thr/Tyr kinase catalytic domain) and IPR020635 (Tyrosine-protein kinase catalytic domain), with the ATP pocket itself annotated by IPR017441 (Protein kinase ATP-binding site) and the catalytic tyrosine-kinase active site by IPR008266. Upstream, the extracellular ligand-binding architecture (IPR000494 Receptor L-domain; IPR006211/IPR006212 furin-like cysteine-rich domain/repeat, the dimerization arm) governs ligand-induced receptor dimerization that erlotinib does not block — it acts purely downstream of dimerization, at the catalytic step. Consistent with quinazoline-class SAR, potency is markedly genotype-dependent: the ChEMBL biochemical record for EGFR (CHEMBL203) reports its highest measured potency, pAct 10.0 (IC50 0.1 nM, "="), against an L858R-mutant assay variant, versus a median pAct of 8.8 across 56 measurements spanning wild-type and mutant constructs — i.e., activating kinase-domain mutants shift affinity into the sub-nanomolar range relative to bulk wild-type activity.

## 3. DOWNSTREAM SIGNALLING
Reactome membership places EGFR at the head of four canonical adaptor/effector branches captured in the retrieved pathway set: GRB2 events in EGFR signaling (R-HSA-179812), SHC1 events in EGFR signaling (R-HSA-180336), the GAB1 signalosome (R-HSA-180292), and PIP3 activates AKT signaling (R-HSA-1257604), all rolling up into the parent "Signaling by EGFR" (R-HSA-177929) and, for activating-mutant receptor, "Constitutive Signaling by Ligand-Responsive EGFR Cancer Variants" (R-HSA-1236382). STRING corroborates the proximal adaptor network with combined scores of 0.999 for SHC1 and SOS1 (RAS-RAF-MEK-ERK entry points) and 0.999 for PIK3CA (PI3K-AKT-mTOR entry point). Bench readouts for pathway engagement, mapped to these axes: RAS-MEK-ERK output [pERK1/2 T202/Y204 Western/phospho-flow]; PI3K-AKT-mTOR output [pAKT S473, pS6 S235/236]; proximal receptor autophosphorylation [pEGFR Y1068/Y1173]. A STAT3 axis is part of established EGFR pharmacology and is reported in the connected literature (PMID 36066408, EGFR-STAT3-ABCB1 signaling) but is not itself a Reactome entry in the retrieved set [pSTAT3 Y705 — established, not Reactome-sourced].

## 4. GENOTYPE -> PHENOTYPE
Sensitizing: the retrieved ChEMBL assay annotation flags L858R as the variant underlying the most potent measured biochemical activity (IC50 0.1 nM) — consistent with exon-19 deletions and L858R being the classical activating kinase-domain lesions that increase ATP-pocket accessibility to anilinoquinazolines and confer erlotinib sensitivity (established EGFR pharmacology; the exon19del genotype itself is not present in the retrieved variant field, only L858R is). Resistance: the gatekeeper substitution T790M and the covalent-inhibitor-blocking C797S are established resistance alterations for this drug class that restore ATP affinity/steric occlusion — neither appears in the retrieved ChEMBL assay_variant_mutation field for CHEMBL203, so they are reported here as established target biology, not as retrieved measurements.

## 5. CELL-LINE MODEL PANEL
Two lines in the ChEMBL cellular data anchor opposite ends of the EGFR-dependence spectrum: A-431 (CHEMBL614069, EGFR-amplified vulvar epidermoid carcinoma) shows IC50 96.0 nM (1 measurement, pAct 7.02), reflecting strong EGFR pathway dependence; NCI-H358 (CHEMBL614135, KRAS-mutant NSCLC) shows IC50 6000.0 nM (1 measurement, pAct 5.22), reflecting EGFR-independent, RAS-driven proliferation that erlotinib cannot suppress at pharmacologically relevant concentrations. The standard EGFR-mutant-lung-cancer panel used to dissect on-target sensitivity/resistance biology — PC9 and HCC827 (exon-19 deletion, EGFR-dependent), H1975 (L858R/T790M, intrinsically resistant), and H358 as a KRAS-mutant negative control — is established cell biology for this target class; only A-431 and H358 among these are present with measured potency values in the retrieved ChEMBL set.

## 6. FUNCTIONAL / EXPERIMENTAL TOOLKIT (established methodology for this target)
- CRISPR knock-in/knockout of EGFR exon-19del, L858R, T790M, C797S in isogenic backgrounds to isolate genotype-specific drug response.
- siRNA/shRNA EGFR knockdown with kinase-dead vs wild-type cDNA rescue to confirm on-target dependence of proliferation/survival phenotypes.
- Phospho-flow or Western time-course/dose-response for pEGFR, pERK, pAKT, pS6 following erlotinib treatment and washout, to define reversibility and rebound kinetics of pathway reactivation.
- Reporter assays for pathway output (ERK-driven AP-1/Elk1 luciferase reporters; FOXO-responsive reporters as an AKT-inhibition readout).
- Co-immunoprecipitation/BRET-FRET dimerization assays probing ERBB2 and ERBB3 heterodimerization, motivated by the STRING partner scores below.
- CBL-dependent ubiquitination/receptor-turnover assays to assess whether EGFR degradation kinetics are altered by kinase-domain mutation or inhibitor engagement.

## 7. ADAPTIVE FEEDBACK & BYPASS BIOLOGY (established target-class biology)
Single-agent EGFR blockade in mutant-driven cells is characteristically transient because of compensatory network rewiring. STRING flags high-confidence EGFR interaction with ERBB2 (score 0.999) and ERBB3 (0.999), consistent with heterodimer-mediated bypass signaling when EGFR catalytic output is suppressed. PIK3CA (STRING 0.999; Reactome R-HSA-1257604, PIP3 activates AKT signaling) marks a parallel route by which activating PIK3CA mutation can sustain AKT output independent of EGFR kinase activity. HGF/MET-axis bypass is a recognized resistance route in this target class; the ChEMBL selectivity data itself shows erlotinib retains only weak off-target affinity for the hepatocyte growth factor receptor/MET (CHEMBL3717, Kd 1100 nM against a Y1235D-variant assay, pAct 5.96), meaning MET reactivation is not suppressed by erlotinib at pharmacologic concentrations. TYRO3/MERTK/AXL-family receptor upregulation is a further established bypass route; erlotinib itself binds TYRO3 (CHEMBL5314, Kd 3900 nM), MER (CHEMBL5331, Kd 980 nM) and UFO/AXL (CHEMBL4895, Kd 4000 nM) only weakly, so these receptors remain catalytically active under erlotinib exposure. STAT3 pathway reactivation as a bypass/resistance node is directly evidenced in the retrieved literature for a related hepatic tumor setting (PMID 36066408, EGFR-STAT3-ABCB1 axis in lenvatinib-resistant HCC), supporting STAT3 as a feedback node relevant to EGFR-inhibitor persistence more broadly.

## 8. SELECTIVITY & POTENCY
Retrieved from ChEMBL (molecule CHEMBL553), pAct = -log10(molar IC50/Ki/Kd); 124 total targets tested.

**Biochemical (SINGLE PROTEIN) targets — most potent**

| Target (ChEMBL ID) | pAct (best) | Metric | Value | n | Variant |
|---|---|---|---|---|---|
| EGFR — CHEMBL203 (primary) | 10.0 | IC50 | 0.1 nM | 56 | L858R |
| Cyclin-G-associated kinase (GAK) — CHEMBL4355 | 8.51 | Kd | 3.1 nM | 4 | — |
| Ser/Thr-protein kinase 10 (STK10) — CHEMBL3981 | 7.72 | Kd | 19.0 nM | 4 | — |
| MAP3K19 — CHEMBL6191 | 7.6 | Kd | 25.0 nM | 1 | — |
| STE20-like kinase (STK4) — CHEMBL4202 | 7.58 | Kd | 26.0 nM | 3 | — |
| ABL1 — CHEMBL1862 | 7.24 (median 6.6) | Kd | 58.0 nM | 30 | H396P |

Long tail: >100 additional SINGLE PROTEIN kinases with best pAct ≤7.02 down to ~5.0 (Kd 100 nM–10 µM range: ERBB2, ERBB4, FLT3, RET, KIT, ABL2, VEGFR2/3, Aurora A/B/C, JAK2/3, PDGFRα/β, ALK, TBK1, and numerous Ser/Thr kinases), consistent with the broad off-target kinome engagement typical of the anilinoquinazoline chemotype.

**Cellular (CELL-LINE, antiproliferation) readouts — representative range**

| Cell line (ChEMBL ID) | pAct | IC50 | n |
|---|---|---|---|
| MCF7 — CHEMBL387 (breast) | 8.0 | 10.0 nM | 8 |
| HepG2 — CHEMBL395 (liver) | 7.1 | 80.0 nM | 2 |
| A-431 — CHEMBL614069 (EGFR-amplified) | 7.02 | 96.0 nM | 1 |
| A549 — CHEMBL392 (lung) | 6.57 | 270.0 nM | 2 |
| NCI-H358 — CHEMBL614135 (KRAS-mutant) | 5.22 | 6000.0 nM | 1 |
| HT-29 / RKO / OVCAR-3 / CWR22R / TE-671 | 4.0 | 100000.0 nM | 1 each |

Cellular potency spans roughly two orders of magnitude across the panel (10 nM to 100 µM), separating EGFR-dependent lines (MCF7, A-431) from EGFR-independent/KRAS-mutant or otherwise pathway-divergent lines (H358 and the 100 µM-plateau group), which is the expected mechanism-consistent signature for an on-target EGFR inhibitor.

## 9. DOSE REGIMES & CELLULAR CONTEXT
The retrieved biochemical/cellular spread — sub-nanomolar EGFR (L858R) IC50, low double-digit-to-triple-digit nanomolar antiproliferation in EGFR-dependent lines (MCF7 10 nM, A-431 96 nM), rising to micromolar in EGFR-independent lines (H358 6000 nM; several lines at 100000 nM) — maps onto the concentration ranges typically used in cellular pathway work: low-to-mid nanomolar for on-target pathway modulation (pEGFR/pERK/pAKT suppression) in EGFR-dependent models, and micromolar exposures required to see any antiproliferative effect in EGFR-independent backgrounds, where activity likely reflects off-pathway or cytotoxic mechanisms rather than EGFR engagement. GTEx expression data place EGFR transcript highest in skin (Skin_Sun_Exposed_Lower_leg median 78.3374 TPM; Skin_Not_Sun_Exposed_Suprapubic 75.9298 TPM) and cultured fibroblasts (60.6276 TPM, GENCODE ENSG00000146648.17), substantially above most other normal tissues in the retrieved panel (e.g., Whole_Blood 0.0450544 TPM) — relevant baseline-expression context for choosing normal-tissue control cells (e.g., primary keratinocytes/fibroblasts) in on-target pharmacodynamic or selectivity counter-screens against the same drug concentrations used in the tumor-line assays above.

```
PROVENANCE
Section 1: pubchem (CID 176870). Section 2: uniprot (P00533), interpro (IPR000494,
IPR000719, IPR001245, IPR006211, IPR006212, IPR008266, IPR017441, IPR020635),
pdb (1M17, 2.6 A, X-ray), chembl (CHEMBL203 assay_variant_mutation field).
Section 3: reactome (R-HSA-177929, R-HSA-179812, R-HSA-180292, R-HSA-180336,
R-HSA-1257604, R-HSA-1236382), string_ppi (SHC1 0.999, SOS1 0.999, PIK3CA 0.999);
STAT3 axis and pSTAT3 readout are established, not Reactome-sourced.
Section 4: chembl (L858R variant field, retrieved); T790M/C797S are established
EGFR pharmacology, not present in the retrieved variant field.
Section 5: chembl (CHEMBL614069 A-431, CHEMBL614135 NCI-H358, verbatim values);
PC9/HCC827/H1975 panel is established cell biology, not in the retrieved set.
Sections 6-7: established EGFR/ErbB pharmacology and functional-genomics workflow,
cross-referenced to string_ppi (ERBB2 0.999, ERBB3 0.999, PIK3CA 0.999), chembl
off-target entries (MET CHEMBL3717, TYRO3 CHEMBL5314, MER CHEMBL5331, UFO
CHEMBL4895), and pubmed (PMID 36066408).
Section 8: chembl selectivity_profile, all pAct/IC50/Kd/n values verbatim.
Section 9: chembl selectivity_profile (dose mapping) and gtex (EGFR expression,
ENSG00000146648.17).
No content in this dossier is drawn from alphafold (entry AF-P00533-F1, pLDDT
75.94, retrieved but not cited above) beyond this note, or from GO-term/PDB
entries (1IVO, 1MOX, 1NQL) not directly used in the mechanism description.
```