# Erlotinib — Diagnostic Pathology Reference

Erlotinib is a first-generation, reversible, ATP-competitive small-molecule inhibitor of the EGFR (epidermal growth factor receptor) intracellular tyrosine kinase domain. As an anilinoquinazoline, it occupies the cytoplasmic ATP-binding cleft of the kinase and does not engage the receptor's extracellular ligand-binding domain — the domain targeted by anti-EGFR monoclonal antibodies (cetuximab, panitumumab) in the same target-drug landscape (Open Targets). Because binding is intracellular and sequence-dependent rather than ectodomain/expression-dependent, no serum biomarker or membrane-expression IHC assay can substitute for tumor genotyping as a predictor of response — eligibility is a genotype call, not an expression call. The pathologist's sign-out is therefore the gatekeeping event for erlotinib use: the tumor must be classified histologically, adequately sampled, genotyped for the guideline-defined EGFR activating alteration, and reported before oncology can act on it.

| Property | Value |
|---|---|
| PubChem CID | 176870 |
| Molecular formula | C22H23N3O4 |
| Molecular weight | 393.4 g/mol |
| IUPAC name | N-(3-ethynylphenyl)-6,7-bis(2-methoxyethoxy)quinazolin-4-amine |
| Metabolism route (established) | Hepatic, predominantly CYP3A4 with minor contribution from CYP1A2 |

## 1. Diagnostic workflow (tissue → eligibility)
The reflex path begins with histologic diagnosis of a non-squamous, non-small cell lung carcinoma (NSCLC) — the disease setting most strongly linked to this target in the retrieved association data (Open Targets: MONDO_0005233 non-small cell lung carcinoma, association score 0.8526; MONDO_0005061 lung adenocarcinoma, score 0.7744). Per established CAP/IASLC/AMP-aligned practice, EGFR mutation testing is triggered reflexively at diagnosis of advanced/metastatic non-squamous NSCLC, ahead of or in parallel with the pathology report, so that a molecular result is available at first oncology consult. Eligibility for erlotinib is tied specifically to detection of a guideline-defined sensitizing EGFR alteration (exon 19 deletion or L858R substitution, established knowledge) in the tumor — expression level, protein overexpression by IHC, or gene amplification are not eligibility criteria for this compound.

## 2. Specimen types & pre-analytics
Adequacy is a pathologist determination (established): core needle or excisional biopsy, or cytology cell block from pleural fluid/EBUS-FNA, fixed in 10% neutral-buffered formalin for 6–24 hours to preserve nucleic acid integrity for downstream molecular testing. Bone metastases requiring decalcification should use EDTA-based (not strong-acid) protocols to avoid DNA degradation that can cause false-negative genotyping. Minimum tumor cellularity for reliable next-generation sequencing (NGS)-based EGFR calls is conventionally ~20% (established, approximate) — cellularity below this threshold should prompt macrodissection, additional sampling, or reflex to a more sensitive PCR-based assay rather than a sign-out of "insufficient."

## 3. Assay platforms
Two assay classes detect the actionable EGFR alterations relevant to erlotinib: targeted NGS panels covering exons 18–21 (detects exon 19 deletions, L858R, exon 20 insertions, T790M in one run) and real-time PCR-based kits validated for EGFR hotspot detection, of which the cobas EGFR Mutation Test v2 is the FDA-recognized companion diagnostic platform for EGFR-TKI eligibility decisions in NSCLC (established). IHC for EGFR protein expression is not a predictive assay for TKI response and is not part of the eligibility workflow for erlotinib. The retrieved ClinVar submissions for this gene do not map cleanly onto this workflow:

| ClinVar ID | Variant | Clinical significance | Review status |
|---|---|---|---|
| 4735901 | c.1214del (p.Leu405fs) | Pathogenic | criteria provided, single submitter |
| 4726907 | c.1823G>A (p.Trp608Ter) | Pathogenic | criteria provided, single submitter |
| 4725069 | c.637del (p.Ile213fs) | Pathogenic | criteria provided, single submitter |
| 4723261 | c.2479del (p.Tyr827fs) | Pathogenic | criteria provided, single submitter |
| 4842914 | c.2101C>T (p.Gln701Ter) | Uncertain significance | criteria provided, single submitter |
| 4842904 | c.3163-15_3183del | Uncertain significance | criteria provided, single submitter |
| 4826848 | c.1232del (p.Pro411fs) | Uncertain significance | criteria provided, single submitter |
| 4824466 | c.1299-2A>G | Uncertain significance | criteria provided, single submitter |

All eight records carry single-submitter review status (one-star equivalent, the lowest formal ClinVar review tier) and none has an associated condition annotation in this pull. None correspond to the canonical exon 19 deletion or L858R responder genotype, nor to the T790M/exon 20 insertion resistance genotypes. These are premature-truncation/frameshift/splice alterations whose relationship to erlotinib eligibility is not established by the retrieved data — they should not be read as either sensitizing or resistance calls; a report encountering one of these would need functional or additional-evidence correlation, not extrapolation from this list.

## 4. Liquid biopsy (plasma ctDNA)
Plasma-based ctDNA NGS or PCR testing for exon 19 deletion/L858R is an accepted reflex or complementary approach (established) when tissue is insufficient or unobtainable, and is particularly used at progression to screen non-invasively for T790M before committing to re-biopsy. A negative plasma result does not exclude a true tissue-positive mutation given variable shedding, so a negative plasma call in a clinically suspicious case should prompt tissue confirmation rather than a stand-alone ineligibility call (established).

## 5. Re-biopsy at progression
Progression on erlotinib is a distinct pathology event requiring re-biopsy (established), primarily to detect acquired T790M — a validated resistance genotype that renders the tumor non-responsive to erlotinib and redirects therapy toward a third-generation EGFR-TKI. Re-biopsy also assesses for histologic transformation (most classically to small-cell carcinoma), a resistance mechanism visible only on repeat tissue sampling and not detectable by genotyping of the original specimen.

## 6. Reporting & quality
Sign-out should report the specific variant using standard HGVS nomenclature, variant allele fraction where the platform provides it, assay limit of detection, and the specific mutation's interpretive category (sensitizing, resistance, or uncertain), rather than a binary "EGFR mutated/wild-type" call. Turnaround time for NGS-based EGFR panels is typically on the order of 5–10 business days in most laboratories (established, approximate); PCR-based single-gene assays are faster and may be used when rapid turnaround is clinically necessary. Participation in external quality assessment for EGFR molecular testing is standard laboratory practice (established).

## Mechanism by genotype (detection-oriented)

| Genotype | Erlotinib eligibility | Basis |
|---|---|---|
| Exon 19 deletion | Eligible — sensitizing | Guideline-defined responder genotype (established); not directly represented in the retrieved ClinVar pull |
| L858R (exon 21) | Eligible — sensitizing | Guideline-defined responder genotype (established); not directly represented in the retrieved ClinVar pull |
| T790M | Not eligible — acquired resistance | Established resistance mechanism; prompts switch to a later-generation TKI |
| Exon 20 insertion | Not eligible — intrinsic resistance | Established; distinct from classical sensitizing alterations |
| ClinVar-retrieved truncating/splice variants (Table above) | Not established either way | Single-submitter review status, no condition annotation; do not extrapolate eligibility from these records |

## Approved use & staging
The strongest disease association in the retrieved data is non-small cell lung carcinoma (score 0.8526) and lung adenocarcinoma (score 0.7744); head and neck squamous cell carcinoma (0.7252) and "lung cancer" (0.7174) are broader EGFR-pathway associations in the same dataset but are not erlotinib's labeled indications. Erlotinib is also approved in combination with gemcitabine for pancreatic cancer (established regulatory knowledge — this indication is not present in the retrieved Open Targets disease list above). Of the 82 EGFR-directed drug candidates returned by Open Targets, erlotinib and erlotinib hydrochloride are both at APPROVAL stage; other approved-stage EGFR small molecules in the same dataset (afatinib, gefitinib, osimertinib, dacomitinib) represent the later-line/next-generation options relevant once a resistance genotype such as T790M emerges.

## Organ toxicity (tissue-level manifestations)
GTEx tissue expression shows EGFR is highest in sun-exposed and non-sun-exposed skin (median 78.3 and 75.9 TPM, respectively) and cultured fibroblasts (60.6 TPM) — consistent with the characteristic acneiform rash that is the dose-limiting toxicity of EGFR-TKIs (established clinical correlate). Moderate GI tract expression (colon transverse 15.0 TPM, sigmoid colon 19.0 TPM) parallels the class-associated diarrhea. Lung expression (22.1 TPM) and liver expression (16.9 TPM) are consistent with the established, less common toxicities of interstitial lung disease/pneumonitis and hepatotoxicity, respectively.

## Combinations & interactions (bedside-relevant)
Because metabolism is CYP3A4-dominant with a CYP1A2 contribution (established), strong CYP3A4 inhibitors or inducers alter erlotinib exposure, and cigarette smoking (a CYP1A2 inducer) lowers erlotinib plasma levels. Gastric acid suppressants (proton pump inhibitors, H2-blockers) reduce absorption because erlotinib solubility is pH-dependent (established). The approved gemcitabine combination in pancreatic cancer is a labeled regimen rather than a pharmacokinetic interaction concern.

## Microenvironment effects on resistance (histology-visible context)
Histologic transformation at progression (most classically small-cell transformation) is a microenvironment/lineage-plasticity resistance mechanism that is visible only on repeat histology, reinforcing the re-biopsy recommendation above (established). The Human Protein Atlas records a large pathology-image inventory for this gene (7,174 total images) spanning multiple normal and tumor tissue categories including breast cancer, though the specific images were not retrieved in this pull (only counts and tissue/location metadata were returned); immunofluorescence subcellular-localization imaging is minimal (1 image on file). These counts confirm broad IHC characterization exists for this target but do not themselves inform erlotinib eligibility, which remains genotype-anchored.

---

**PROVENANCE**
- Retrieved: PubChem (CID 176870 — formula, MW, IUPAC name, SMILES); ClinVar (8 EGFR variant records — IDs, clinical significance, review status); Open Targets (ENSG00000146648 — disease associations with scores; 82 drug candidates with max clinical stage); GTEx (ENSG00000146648.17 — tissue-level median TPM); UniProt (P00533 — subcellular GO terms); Human Protein Atlas (ENSG00000146648 — pathology image count 7,174, microscopy image count 1, tissue/location lists; image URLs withheld per include_images=false); PubMed (PMID 40554308 — erlotinib-aptamer targeting of wild-type and resistant EGFR in NSCLC; PMID 24051929 — afatinib/erlotinib/gefitinib first-line therapy in EGFR-mutant lung adenocarcinoma). Other returned PubMed records (PMID 36344490, 36066408, 32335942) concerned sepsis macrophage biology or hepatocellular carcinoma and were outside this target's approved NSCLC diagnostic/eligibility setting and excluded.
- Established diagnostic-pathology knowledge (not connector-retrieved, standard clinical/regulatory knowledge): CAP/IASLC/AMP-aligned reflex-testing workflow; specimen fixation and decalcification practice; minimum cellularity threshold; cobas EGFR Mutation Test v2 as companion diagnostic; sensitizing (exon 19 del, L858R) vs resistance (T790M, exon 20 insertion) genotype definitions; plasma ctDNA use; re-biopsy-at-progression practice; reporting/turnaround conventions; CYP3A4/CYP1A2 metabolism and interaction profile; organ toxicity mechanisms; pancreatic cancer indication.