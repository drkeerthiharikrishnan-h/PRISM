# Erlotinib — Computational Structural & Systems Profile
First-generation reversible EGFR tyrosine kinase inhibitor characterized here across ligand physicochemistry, the 1M17 co-crystal contact geometry, EGFR domain/network context, and disease association evidence.

## 1. Molecular constitution (modeling-relevant descriptors)

| Descriptor | Erlotinib | Source |
|---|---|---|
| Formula | C22H23N3O4 | rdkit_descriptors |
| MW | 393.44 | rdkit_descriptors |
| Crippen cLogP | 3.41 | rdkit_descriptors |
| TPSA | 74.73 Å² | rdkit_descriptors |
| HBD / HBA | 1 / 7 | rdkit_descriptors |
| Rotatable bonds | 10 | rdkit_descriptors |
| Aromatic rings | 3 | rdkit_descriptors |
| Fraction Csp3 | 0.273 | rdkit_descriptors |
| Heavy atoms | 29 | rdkit_descriptors |
| QED (weighted) | 0.42 | rdkit_descriptors |
| Lipinski / Veber | pass / pass (0 violations) | rdkit_descriptors |
| ESOL logS / solubility | −4.17 / 26.4 mg L⁻¹ (67.2 µM) | rdkit_descriptors |
| PAINS alerts | none matched | rdkit_descriptors |
| InChIKey | AAKJLRGGTJKAMG-UHFFFAOYSA-N | rdkit_descriptors |
| PubChem CID | 176870 | rdkit_descriptors |

With fraction Csp3 = 0.273 and only three aromatic rings but a low sp3 fraction, erlotinib is a largely flat, extended molecule; 10 rotatable bonds (mostly the two morpholino-ethoxy side chains) give it more conformational freedom than the gefitinib comparator (8 rotatable bonds, fCsp3 0.364, Section 6) despite similar ring count. TPSA (74.73 Å²) and a single HBD are consistent with the single hinge-donor binding mode described in Section 2. Zero Lipinski/Veber violations and no PAINS hits support use as a clean docking/rescoring reference ligand.

## 2. Target binding structure & interactions (PDB 1M17)

Co-crystal: EGFR kinase domain with ligand AQ4 (erlotinib), contact cutoff 4.5 Å, 17 total contacts (pdb connector). Legacy PDB numbering and UniProt (modern) numbering differ by a fixed **+24 offset** (modern = legacy + 24), reported verbatim below. Resolution and experimental method were not returned in this connector pull (not reported).

**Hinge hydrogen bond:** Met769 (legacy) / **Met793** (modern) — ligand atom N2 to protein backbone N, min. distance **2.70 Å**, classified H-bond/polar. This is the canonical hinge-binding contact anchoring the quinazoline N1 to the Met793 backbone amide.

**Gatekeeper contact:** Thr766 (legacy) / **Thr790** (modern) — ligand atom C1 to protein OG1, min. distance **3.41 Å**, classified polar contact. This residue position (modern 790) is the EGFR gatekeeper threonine.

Additional polar/H-bond contacts from the table (legacy→modern, distance): Gln767→791 (3.15 Å, polar), Gly772→796 (3.24 Å, H-bond/polar), Leu694→718 (3.27 Å, H-bond/polar), Phe771→795 (3.45 Å, polar), Leu768→792 (3.50 Å, polar), Asp831→855 (3.11 Å, polar), Pro770→794 (3.11 Å, polar), Thr830→854 (3.65 Å, hydrophobic/vdW).

Remaining hydrophobic/van der Waals contacts (6 of the 17) — Ala719→743, Leu764→788, Leu820→844, Glu738→762, Val702→726, Ile765→789 — span 3.31–4.45 Å and line the adenine-pocket/back-hydrophobic-channel wall accommodating the m-ethynylphenyl and dimethoxy-ethoxy substituents.

## 3. Sensitizing & resistance mutations (sequence → structure → phenotype)

*Established EGFR pharmacology, not returned by a connector; mapped onto the retrieved modern numbering where the contact table provides a structural anchor.*

- **Sensitizing:** exon 19 in-frame deletions (e.g., delE746–A750) and the exon 21 point mutation L858R destabilize the inactive kinase conformation, increasing ATP-pocket accessibility and erlotinib affinity relative to wild-type; these are the classical erlotinib-responsive genotypes in non-small cell lung carcinoma.
- **Resistance — T790M:** substitution at the gatekeeper position. Notably, the retrieved contact table's gatekeeper residue, Thr766 (legacy) / **Thr790 (modern)**, is exactly the T790M numbering — the connector-derived contact geometry directly localizes where this resistance mutation acts. T790M increases steric bulk at the pocket wall contacted by ligand atom C1 (3.41 Å in the wild-type structure) and raises ATP affinity, together reducing erlotinib potency; it is the dominant acquired-resistance mechanism after first-generation EGFR-TKI therapy.
- **Resistance — C797S:** relevant to later-line, covalent third-generation inhibitors (not erlotinib, which binds reversibly); abolishes the cysteine nucleophile these agents require, and is mentioned here only for treatment-sequence context, not as a mechanism affecting erlotinib's own reversible binding mode.

No ClinVar or structural-variant connector data were retrieved for these mutations in this pull; the above is established mechanistic knowledge, not connector-verified.

## 4. Downstream signaling & cellular effects

UniProt (P00533) returns a function annotation limited to a "microbial infection" comment (EGFR as an HCV hepatocyte entry co-receptor via CD81–CLDN1 complex formation) and eight cellular-component GO terms (e.g., GO:0009986 cell surface, GO:0005789 endoplasmic reticulum membrane, GO:0031901 early endosome membrane); sequence length, binding sites, and domain fields were empty (not reported). This retrieved excerpt does **not** capture EGFR's canonical growth-factor receptor tyrosine kinase role — that is supplied here as established knowledge, not from this connector call, and should not be treated as contradicting the canonical function.

STRING returns EGFR partners at combined score 0.999 for PTPN11, HBEGF, NRG1, TGFA, ERBB2, DCN, SHC1, SOS1, PIK3CA, and ERBB3 (score-aware ranking: all at the top confidence band, 0.999). Reactome places EGFR in *Signaling by EGFR* (R-HSA-177929), *Constitutive Signaling by Ligand-Responsive EGFR Cancer Variants* (R-HSA-1236382), *GRB2 events in EGFR signaling* (R-HSA-179812), *SHC1 events in EGFR signaling* (R-HSA-180336), *GAB1 signalosome* (R-HSA-180292), and *PIP3 activates AKT signaling* (R-HSA-1257604), plus ERBB2/ERBB4 paralog pathways. Integrating STRING and Reactome (established mechanistic layer on top of these retrieved IDs): ligand-bound EGFR recruits GRB2–SOS1 to activate RAS-MAPK, and SHC1/GAB1–PIK3CA to activate PI3K-AKT; PTPN11 (SHP2) is a shared adaptor feeding both arms. Erlotinib, by occupying the ATP site documented in Section 2, blocks autophosphorylation and attenuates both branches in EGFR-driven tumors.

## 5. Structural basis of potency & engineering directions

Potency rests on the single hinge H-bond (Met793, 2.70 Å) combined with a large hydrophobic back-pocket contact surface (Ala743, Leu788, Ile789, Val726, Leu844, Glu762) rather than multiple polar anchors — consistent with HBD = 1 and TPSA 74.73 Å² from Section 1. The wild-type Thr790 gatekeeper (3.41 Å polar contact) leaves room for the m-ethynylphenyl group; T790M narrows this space (Section 3), rationalizing loss of potency without a connector-confirmed binding assay for the mutant in this pull. Engineering directions consistent with the retrieved descriptor/contact profile: (i) reduce the 10 rotatable bonds (entropic penalty) by cyclizing one dimethoxy-ethoxy chain while preserving the two furthest-out oxygens that make the Gly796/Leu718-region polar contacts; (ii) introduce an electrophile positioned toward Cys797 (one hinge-turn beyond Met793) to gain covalent, mutation-resistant engagement, the strategy used in later-generation EGFR-TKIs; (iii) modify the ethynyl-phenyl terminus to better fill the Ala743/Leu788 hydrophobic contacts and offset the affinity loss from a T790M-narrowed pocket.

## 6. Erlotinib vs gefitinib (structural / binding view)

| Property | Erlotinib | Gefitinib |
|---|---|---|
| Formula | C22H23N3O4 | C22H24ClFN4O3 |
| MW | 393.44 | 446.91 |
| cLogP | 3.41 | 4.28 |
| TPSA | 74.73 | 68.74 |
| HBD / HBA | 1 / 7 | 1 / 7 |
| Rotatable bonds | 10 | 8 |
| Aromatic rings | 3 | 3 |
| Fraction Csp3 | 0.273 | 0.364 |
| QED | 0.42 | 0.52 |
| ESOL solubility | 26.4 mg/L (67.2 µM) | 3.1 mg/L (6.9 µM) |
| PAINS | none | none |
| InChIKey | AAKJLRGGTJKAMG-UHFFFAOYSA-N | XGALLCVXEZPNRQ-UHFFFAOYSA-N |

Both share the 4-anilinoquinazoline hinge-binding core (1 HBD/7 HBA) and are expected to make an equivalent Met793-hinge H-bond, but gefitinib's chloro-fluoro-anilino group and morpholino-propoxy chain raise cLogP (4.28 vs 3.41) and lower predicted aqueous solubility roughly 10-fold (ESOL 6.9 µM vs 67.2 µM) relative to erlotinib, while gefitinib's higher fCsp3 (0.364 vs 0.273) and fewer rotatable bonds (8 vs 10) give it a more compact, higher-QED profile (0.52 vs 0.42). No PDB contact table for a gefitinib co-crystal was retrieved in this pull, so residue-level comparison of the two hinge/gatekeeper interactions is not reported.

## 7. Computational approaches & suggested next steps

*Established computational-chemistry practice, not connector output.* (i) Redock AQ4/erlotinib into 1M17 and cross-dock into a T790M homology/mutant model to quantify the gatekeeper steric clash implied by the 3.41 Å wild-type contact. (ii) Run MD (100 ns–µs scale) on the hinge region to test persistence of the Met793 H-bond and Thr790 contact under thermal fluctuation. (iii) Use FEP/TI to estimate the ΔΔG of erlotinib binding for T790M and L858R/T790M double mutants relative to wild-type, calibrated against the wild-type contact geometry reported here. (iv) MM-GBSA rescoring of docking poses using the retrieved hydrophobic contact set (Ala743, Leu788, Ile789, Val726, Leu844, Glu762) as a per-residue decomposition checklist. (v) Given the AlphaFold model's global pLDDT of 75.94 (AF-P00533-F1, moderate-confidence, whole-chain average), prioritize the experimental 1M17 kinase-domain coordinates for docking/MD over the AlphaFold model in this region; if extending to non-crystallized domains, treat per-residue pLDDT (not retrieved here) as the confidence filter before modeling.

---
**PROVENANCE**
- RETRIEVED (verbatim): Section 1 — rdkit_descriptors (erlotinib block + gefitinib comparison block). Section 2 — pdb (1M17, ligand AQ4, contact table, +24 legacy→modern offset). Section 3 — modern residue number 790 cross-referenced from the pdb contact table only; mutation identities/phenotypes are established knowledge. Section 4 — uniprot (P00533 function text and GO terms, noted as a partial/non-canonical excerpt), interpro (domain list, 12 of reported entry_count 15 entries returned), string_ppi (10 partners, combined score 0.999 each), reactome (10 pathway IDs). Section 5 — descriptor/contact values as above. Section 6 — rdkit_descriptors comparator block (gefitinib). Disease/asset context referenced in text: opentargets (ENSG00000146648; NSCLC 0.8526, lung adenocarcinoma 0.7744, cancer 0.7369, HNSCC 0.7252, lung cancer 0.7174; 82 drug candidates including ERLOTINIB and GEFITINIB at APPROVAL stage). Literature: pubmed PMIDs 36344490, 40554308, 36066408, 32335942, 24051929 (cited as available literature; not directly quoted for mechanistic claims above beyond general topical relevance).
- ESTABLISHED (labeled, not connector-sourced): EGFR canonical RTK/MAPK-PI3K-AKT signaling mechanism (Section 4), exon19del/L858R/T790M/C797S mutation identities and phenotypes (Section 3), structure-potency rationale and engineering strategies (Section 5), computational workflow recommendations (Section 7).
- NOT REPORTED: PDB 1M17 resolution/method fields; UniProt sequence_length/binding_sites/domains; 3 of 15 InterPro entries; any gefitinib-specific PDB contact table; ClinVar entries for T790M/C797S/L858R.