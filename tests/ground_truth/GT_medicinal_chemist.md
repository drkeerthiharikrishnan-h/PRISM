```
ERLOTINIB — MEDICINAL-CHEMISTRY ENRICHED PROFILE
Reversible ATP-competitive EGFR tyrosine-kinase inhibitor (4-anilinoquinazoline class)
Base: ChEMBL CHEMBL553 / target CHEMBL203 (EGFR) + med-chem layer added. Descriptors
by RDKit (rdkit_descriptors connector). PK/ADMET from established clinical pharmacology.
PubChem CID 176870. InChIKey AAKJLRGGTJKAMG-UHFFFAOYSA-N.

--------------------------------------------------------------------------------
7 · PHYSICOCHEMISTRY & DRUGGABILITY (RDKit-computed)
--------------------------------------------------------------------------------
Formula C22H23N3O4, MW 393.44 (PubChem/RDKit agree). SMILES (PubChem):
COCCOC1=C(C=C2C(=C1)C(=NC=N2)NC3=CC=CC(=C3)C#C)OCCOC.

Property                    | Value          | Confidence
----------------------------|----------------|-----------------------------
Crippen cLogP                | 3.41           | high (RDKit-computed)
TPSA                         | 74.73 A^2      | high (RDKit-computed)
HBD / HBA                    | 1 / 7          | high (RDKit-computed)
Rotatable bonds              | 10             | high (RDKit-computed)
Aromatic rings                | 3              | high (RDKit-computed)
Fraction Csp3                | 0.273          | high (RDKit-computed)
Heavy atom count              | 29             | high (RDKit-computed)
QED (weighted)                | 0.42           | high (RDKit-computed)
Lipinski violations           | 0 (pass)       | high (RDKit-computed)
Veber pass                    | Yes            | high (RDKit-computed)
Ro3 pass (fragment-like)      | No (ADMET)     | high (admet connector)
PAINS / frequent-hitter match | none flagged   | high (RDKit substructure screen)

The molecule is fully Lipinski- and Veber-compliant, but QED (0.42) sits only in the
mid-range — driven by the high rotatable-bond count (10) and the two flexible
methoxyethoxy side chains, which cost conformational entropy on binding despite
acceptable size and polarity. Three aromatic rings and a rigid quinazoline hinge give
the fraction Csp3 a low value (0.273), typical of the anilinoquinazoline chemotype and
consistent with kinase-hinge planarity requirements rather than a flag.

--------------------------------------------------------------------------------
8 · SOLUBILITY & pH DEPENDENCE (the central formulation problem)
--------------------------------------------------------------------------------
ESOL (Delaney) estimate: logS -4.17 (RDKit), corresponding to 26.4 mg/L / 67.2 uM —
intrinsically low-to-moderate aqueous solubility for a 393 Da compound.

Established pharmacology (not RDKit-derived): erlotinib is a weak base with a
quinazoline N1 pKa ~5.4 (est.), giving markedly pH-dependent solubility — solubility
is highest under acidic conditions and drops sharply above pH ~5-6. This places the
compound as BCS Class II (est.) — low solubility, high permeability — and is the
mechanistic basis for the well-documented drug interaction in which gastric
acid-reducing agents (proton-pump inhibitors, H2-antagonists) reduce erlotinib
absorption and systemic exposure by removing the acidic micro-environment needed for
dissolution. This pH-dependence, not a permeability limitation, is the dominant
formulation liability for this chemotype.

Relative to the resolved same-class comparator gefitinib (ESOL logS -5.16, 3.1 mg/L,
6.9 uM), erlotinib's RDKit-estimated solubility is calculated as higher (~10x on a
molar basis) despite similar TPSA (74.7 vs 68.7 A^2) and comparable HBD/HBA (1/7 vs
1/7) — attributable to erlotinib's bis(methoxyethoxy) ether side chains being smaller
and less lipophilic than gefitinib's morpholinopropoxy chain in the RDKit Crippen
model (3.41 vs 4.28 cLogP), even though gefitinib carries an ionizable morpholine
that in practice aids solubility at gastric pH. The two compounds share the same
pH-dependent-absorption liability class.

--------------------------------------------------------------------------------
9 · LIGAND EFFICIENCY & POTENCY QUALITY (RDKit + ChEMBL potencies)
--------------------------------------------------------------------------------
Primary target: EGFR (CHEMBL203), assay context flagged with the L858R activating
mutation. best_pact = 10.0 (representative IC50 = 0.1 nM, "="), median_pact = 8.8
across n = 56 measurements — a wide spread reflecting heterogeneous assay formats
(enzymatic vs cellular, WT vs mutant EGFR) pooled under one target entry; the
best-case value corresponds to a sensitized mutant, not necessarily WT-EGFR biochemical
IC50.

Ligand-efficiency metrics (rdkit_descriptors, context "erlotinib @ Epidermal growth
factor receptor", pIC50 10.0 fixed to the best_pact record):

Metric | Value | Interpretation
-------|-------|----------------------------------------------------------------
LE     | 0.47  | strong binding-energy-per-heavy-atom for a 29-heavy-atom ligand
LLE/LipE | 6.59 | good potency-per-lipophilicity-unit; > 5 is generally favorable
LELP   | 7.2   | moderate — lipophilicity contribution is non-trivial relative to LE

At LE 0.47 / LLE 6.59, erlotinib sits in the efficient-lead territory typical of
approved kinase inhibitors; LELP 7.2 (formally cLogP/LE) signals that a meaningful
share of potency is carried by lipophilicity rather than pure shape complementarity —
consistent with the compound's mid-range QED (0.42) despite excellent nominal potency.

Selectivity context — best_pact across the retrieved kinome panel (n=124 targets total):

Target                          | best_pact | Representative value | Mutation
---------------------------------|-----------|------------------------|----------
EGFR (primary)                   | 10.0      | IC50 0.1 nM            | L858R
Cyclin-G-associated kinase (GAK)  | 8.51      | Kd 3.1 nM              | none
STK10                             | 7.72      | Kd 19 nM               | none
ABL1                              | 7.24      | Kd 58 nM (median 6.6)  | H396P
ErbB-2 (HER2)                     | 6.92      | IC50 120 nM (median 6.29)| none
FLT3                              | 6.89      | Kd 130 nM (median 6.3) | D835Y
KIT                               | 5.89      | Kd 1300 nM (median 5.8)| V559D,T670I

On the L858R-sensitized best-case reading, EGFR is ~30-fold more potent than the next
strongest off-target hit (GAK) and >200-fold over ErbB-2/FLT3, supporting a genuine
EGFR-directed selectivity window; however, several off-targets (GAK, STK10, ABL1) sit
within 2-3 log units and are supported by only 1-4 measurements each, so their
precision is low. Cellular antiproliferation potency in EGFR-overexpressing lines
(MCF7 best_pact 8.0, A-431 7.02, HepG2 7.1) is 1-3 orders weaker than the biochemical
best_pact, consistent with cell-permeability/efflux and target-expression effects
rather than a change in intrinsic affinity. The long tail of cell-line entries with
best_pact ≤ 4.5 (e.g. HT-29, RKO, OVCAR-3, all IC50 = 100 uM, n=1 each) reflects
EGFR-independent, low-relevance cytotoxicity screens and should not be read as
off-target liabilities.

--------------------------------------------------------------------------------
10 · ADME / PHARMACOKINETICS (human) — established clinical pharmacology
--------------------------------------------------------------------------------
The following are established/textbook pharmacology values (not RDKit/ChEMBL fields);
approximate values are marked "~"/"est.":
- Oral bioavailability: ~60% (est.), reduced by acid-reducing co-medications (see §8).
- Metabolism: predominantly hepatic CYP3A4, minor contribution from CYP1A2; major
  active metabolite OSI-420 retains EGFR-inhibitory activity (est.).
- Plasma protein binding: high, ~93-95% (est.), primarily to albumin and alpha-1 acid
  glycoprotein.
- Elimination half-life: ~36 hours (est.), supporting once-daily oral dosing.
- Route of elimination: predominantly fecal/biliary, minor renal component (est.).
- max_phase (ADMET connector, CHEMBL553): 4.0 — approved drug, consistent with
  Open Targets listing ERLOTINIB at max_clinical_stage APPROVAL for EGFR.

--------------------------------------------------------------------------------
11 · ADMET LIABILITIES & SAFETY-RELEVANT CHEMISTRY
--------------------------------------------------------------------------------
No PAINS/frequent-hitter alerts were flagged by the RDKit substructure screen
(pains_alerts.match = false), so acute assay-artifact risk from reactive/promiscuous
substructures is low; the terminal alkyne and quinazoline core are not canonical PAINS
motifs.

Established, class-level liabilities (clinical pharmacology, not connector-derived):
- CYP3A4-mediated drug-drug interactions: strong CYP3A4 inhibitors/inducers and
  smoking (CYP1A2 induction) alter systemic exposure materially (est.).
- pH-dependent absorption liability described in §8 (acid-reducing agents).
- Class-associated adverse effects for EGFR-TKIs of this scaffold: acneiform rash,
  diarrhea, hepatotoxicity, and interstitial lung disease (rare but boxed-label class
  concern) (est.); these are on-target/off-target class effects, not connector fields.
- No structural alerts for reactive metabolite formation are evident from the RDKit
  screen, but CYP3A4-mediated oxidative metabolism of the anilinoquinazoline/ethynyl
  motif is the established bioactivation-adjacent pathway to monitor (est.).

--------------------------------------------------------------------------------
12 · STRUCTURE-ACTIVITY RELATIONSHIPS (what each region does)
--------------------------------------------------------------------------------
- Quinazoline N1/N3 core: the canonical hinge-binding motif for Type-I ATP-competitive
  EGFR inhibitors; retained across the whole 4-anilinoquinazoline series (gefitinib,
  afatinib) and essential for the sub-nM EGFR potency reported here (est., supported
  by PDB 1M17 co-crystal, see §14).
- 4-anilino / 3-ethynylphenyl tail: occupies the hydrophobic back pocket adjacent to
  the gatekeeper; the meta-ethynyl substituent is a compact, planar group whose size
  and electronics are tuned for the EGFR pocket — this region is the primary
  determinant of the erlotinib/gefitinib potency and selectivity difference (est.).
- 6,7-bis(2-methoxyethoxy) side chains: solvent-exposed substituents on the quinazoline
  ring; RDKit shows these give erlotinib 10 rotatable bonds and fraction Csp3 0.273,
  and drive the cLogP/TPSA/solubility profile that differentiates it from gefitinib's
  morpholinopropoxy chain (comparator block, §8-9). This region is the main SAR handle
  for tuning solubility and PK without perturbing the hinge-binding pharmacophore
  (est.).
- Terminal alkyne: a compact, low-steric-demand terminus rather than a reactive
  warhead in this context; also a synthetically convenient handle for downstream
  bioconjugation (see §14; supported by PMID 40554308).

--------------------------------------------------------------------------------
13 · SYNTHESIS-RELEVANT HANDLES
--------------------------------------------------------------------------------
Established route logic (est., standard for this chemotype, no fabricated specifics):
- Quinazoline core is typically assembled via Niementowski-type cyclization or Dimroth
  rearrangement from an appropriately substituted anthranilic-acid/formamidine
  precursor bearing the two catechol-derived oxygens.
- The 6,7-dihydroxy (catechol) precursor is alkylated by Williamson ether synthesis
  with 2-methoxyethyl halide/tosylate to install both methoxyethoxy chains — this step
  is the natural point for analog diversification of the solvent-exposed region
  (§12).
- A 4-chloroquinazoline intermediate undergoes nucleophilic aromatic substitution with
  3-ethynylaniline to install the anilino linkage — the key convergent bond-forming
  step.
- The terminal alkyne is retained through the synthesis and is directly usable for
  copper-catalyzed azide-alkyne cycloaddition (click chemistry) without further
  functionalization — a practical handle for probe or conjugate synthesis (est.,
  consistent with the aptamer-conjugate chemistry reported in PMID 40554308).

--------------------------------------------------------------------------------
14 · ADC / CONJUGATE CONSIDERATIONS
--------------------------------------------------------------------------------
Erlotinib is not used as a classical antibody-drug-conjugate (ADC) cytotoxic payload:
its EGFR IC50, while sub-nanomolar in the sensitized-mutant assay context (best_pact
10.0), is a reversible, ATP-competitive mechanism rather than the picomolar,
irreversible cytotoxicity (e.g., microtubule or DNA-damaging payloads) generally
required of ADC warheads, and no ADC-format record appears among the retrieved
Open Targets drug candidates for EGFR (candidates in that list are predominantly
antibodies, TKIs, or antibody-payload conjugates using unrelated cytotoxic warheads,
e.g. DEPATUXIZUMAB MAFODOTIN, CETUXIMAB SAROTALOCAN, LOSATUXIZUMAB VEDOTIN).

The one retrieved literature precedent for erlotinib bioconjugation is a lysosome-
targeting chimera (PMID 40554308), which uses erlotinib itself as the EGFR-binding
"warhead" tethered via its terminal alkyne to an IGF2R-targeting aptamer, exploiting
target degradation rather than cytotoxic payload delivery — a distinct conjugate
strategy from ADC cytotoxin delivery. This is the only conjugate-relevant use case
supported by the retrieved data; no other ADC/linker/payload information was returned.

================================================================================
PROVENANCE
================================================================================
RETRIEVED (verbatim): PubChem (CID 176870, SMILES, formula, MW, IUPAC name); RDKit
descriptor block and ESOL estimate (rdkit_descriptors connector, §7-9); ligand
efficiency (LE/LLE/LELP) and gefitinib comparator block (rdkit_descriptors, §8-9);
ChEMBL potency/selectivity table (CHEMBL553 vs CHEMBL203 and off-targets, §9); ADMET
fields (max_phase, Ro5/Ro3, QED, CHEMBL553, §10); Open Targets disease association
scores and EGFR drug-candidate landscape (ENSG00000146648, §14); PDB structures
(1IVO, 1M14, 1M17, 1MOX, 1NQL, §14 reference below); PubMed abstracts (PMIDs
36344490, 40554308, 36066408, 32335942, 24051929, §12/§14).

ESTABLISHED clinical pharmacology / med-chem (labeled "est." inline): pKa/BCS class
and pH-dependent solubility mechanism (§8); human ADME — CYP3A4/1A2 metabolism, oral
F, protein binding, half-life (§10); class-level ADMET liabilities and DDI mechanisms
(§11); SAR-by-region rationale and synthesis route logic (§12-13); ADC/conjugate
mechanistic distinction (§14). No fabricated identifiers, PMIDs, or precise measured
numbers were introduced in the established-knowledge layer.

Binding-site structural context: PDB 1M17 (2.6 A, X-ray) is the EGFR tyrosine-kinase
domain co-crystallized specifically with erlotinib; 1M14 (2.6 A) is the unliganded/
alternative EGFR kinase domain; 1IVO (3.3 A), 1MOX (2.5 A), 1NQL (2.8 A) are EGFR
extracellular-domain structures (ligand/TGF-alpha/EGF complexes) included for
receptor-architecture context, not inhibitor binding mode.
```