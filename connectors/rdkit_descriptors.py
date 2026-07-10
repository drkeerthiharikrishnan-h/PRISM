"""RDKit descriptor connector — offline, open-source physicochemistry + ligand efficiency.

Computes the medicinal-chemistry / computational-chemistry descriptor layer that the
ChEMBL `molecule_properties` block cannot supply: Crippen cLogP, TPSA, fraction Csp3,
QED, InChIKey, Lipinski + Veber rule flags, a PAINS/frequent-hitter screen, heavy-atom
count, and an ESOL (Delaney) aqueous-solubility estimate. When ChEMBL potency values
(pIC50) are supplied it also computes ligand efficiency metrics (LE, LLE/LipE, LELP).

Everything here is deterministic local compute from a SMILES string — nothing is
fabricated. The SMILES is taken from the entity map (populated by the PubChem connector)
or resolved from PubChem by CID / name as a fallback.

Image policy: a 2D depiction URL is returned ONLY when params["include_images"] is true.
"""
from typing import Optional
import math

import httpx

from connectors.utils import retryable_get

PUBCHEM = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

# Known comparator SMILES so a persona can request a side-by-side without a second
# network round-trip. Values are canonical PubChem SMILES.
_KNOWN_SMILES = {
    "gefitinib": "COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1",
    "erlotinib": "C#Cc1cccc(Nc2ncnc3cc(OCCOC)c(OCCOC)cc23)c1",
}


async def fetch(entity_ids: dict, params: dict) -> dict:
    """
    entity_ids:
      smiles        : SMILES string (preferred; usually threaded from PubChem)
      drug_pubchem  : PubChem CID (fallback lookup)
      entity        : compound name (fallback lookup)
    params:
      pIC50_values  : dict[label -> pIC50]  → adds ligand-efficiency block
      comparators   : list[str] of names/SMILES  → adds side-by-side descriptor rows
      include_images: bool (default False)  → adds gated 2D depiction URL
    Returns descriptor dict (see _describe) plus optional ligand_efficiency / comparison.
    """
    smiles = entity_ids.get("smiles")
    cid = entity_ids.get("drug_pubchem")
    name = (entity_ids.get("entity") or "").strip()

    if not smiles and name and name.lower() in _KNOWN_SMILES:
        smiles = _KNOWN_SMILES[name.lower()]
    if not smiles:
        smiles = await _resolve_smiles(cid, name)
    if not smiles:
        return {"error": "no SMILES resolved for compound"}

    include_images = bool(params.get("include_images", False))
    result = _describe(smiles, name or None, cid, include_images)
    if "error" in result:
        return result

    # Ligand efficiency, if potencies were supplied. These come from the resolved
    # entity map (orchestrator threads the primary-target pAct from ChEMBL) or from
    # explicit params — never hardcoded per drug in a persona.
    pic50_values = params.get("pIC50_values") or entity_ids.get("pIC50_values") or {}
    if pic50_values:
        result["ligand_efficiency"] = _ligand_efficiency(result, pic50_values)

    # Comparator side-by-side (same-target drug[s]); resolver populates entity_ids,
    # a caller may override via params. Any name is resolved to SMILES via PubChem.
    comparators = params.get("comparators") or entity_ids.get("comparators") or []
    if comparators:
        comp_rows = []
        for comp in comparators:
            comp_smiles = _KNOWN_SMILES.get(str(comp).lower())
            if not comp_smiles:
                comp_smiles = await _resolve_smiles(None, str(comp))
            if comp_smiles:
                row = _describe(comp_smiles, str(comp), None, include_images)
                comp_rows.append(row)
        if comp_rows:
            result["comparison"] = comp_rows

    return result


# --------------------------------------------------------------------------- #
# Core descriptor computation
# --------------------------------------------------------------------------- #
def _describe(smiles: str, name: Optional[str], cid, include_images: bool) -> dict:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, Crippen, rdMolDescriptors, QED

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {"error": f"RDKit could not parse SMILES: {smiles}"}

    mw = Descriptors.MolWt(mol)
    clogp = Crippen.MolLogP(mol)
    tpsa = rdMolDescriptors.CalcTPSA(mol)
    hbd = rdMolDescriptors.CalcNumHBD(mol)
    hba = rdMolDescriptors.CalcNumHBA(mol)
    rotb = rdMolDescriptors.CalcNumRotatableBonds(mol)
    arom_rings = rdMolDescriptors.CalcNumAromaticRings(mol)
    fsp3 = rdMolDescriptors.CalcFractionCSP3(mol)
    hac = mol.GetNumHeavyAtoms()
    qed = QED.qed(mol)
    formula = rdMolDescriptors.CalcMolFormula(mol)
    try:
        inchikey = Chem.MolToInchiKey(mol)
    except Exception:
        inchikey = ""

    # Lipinski Ro5: violations of (MW<=500, cLogP<=5, HBD<=5, HBA<=10)
    ro5_flags = [mw > 500, clogp > 5, hbd > 5, hba > 10]
    ro5_viol = sum(ro5_flags)
    # Veber: RotB <= 10 and TPSA <= 140
    veber_pass = (rotb <= 10) and (tpsa <= 140)

    out = {
        "smiles": smiles,
        "molecular_formula": formula,
        "molecular_weight": round(mw, 2),
        "clogp_crippen": round(clogp, 2),
        "tpsa": round(tpsa, 2),
        "hbd": hbd,
        "hba": hba,
        "rotatable_bonds": rotb,
        "aromatic_rings": arom_rings,
        "fraction_csp3": round(fsp3, 3),
        "heavy_atom_count": hac,
        "qed_weighted": round(qed, 2),
        "inchikey": inchikey,
        "lipinski_violations": ro5_viol,
        "lipinski_pass": ro5_viol == 0,
        "veber_pass": veber_pass,
        "esol_logs_molar": None,
        "esol_solubility_mg_per_l": None,
        "esol_solubility_uM": None,
        "pains_alerts": _pains(mol),
    }
    if name:
        out["name"] = name
    if cid:
        out["cid"] = cid

    # ESOL (Delaney) intrinsic aqueous solubility of the neutral species.
    esol = _esol(mol, clogp, mw, rotb)
    out["esol_logs_molar"] = round(esol, 2)
    sol_molar = 10 ** esol
    out["esol_solubility_mg_per_l"] = round(sol_molar * mw * 1000, 1)  # mol/L * g/mol * 1000 = mg/L
    out["esol_solubility_uM"] = round(sol_molar * 1e6, 1)

    if include_images:
        # PubChem PNG depiction (renderable) — only when explicitly requested.
        if cid:
            out["depiction_url"] = f"{PUBCHEM}/compound/cid/{cid}/PNG"
        else:
            out["depiction_url"] = (
                f"{PUBCHEM}/compound/smiles/{smiles}/PNG"
            )
    return out


def _esol(mol, clogp: float, mw: float, rotb: int) -> float:
    """Delaney ESOL: log10(solubility in mol/L) of the neutral species."""
    heavy = mol.GetNumHeavyAtoms()
    aromatic_atoms = sum(1 for a in mol.GetAtoms() if a.GetIsAromatic())
    ap = (aromatic_atoms / heavy) if heavy else 0.0
    return 0.16 - 0.63 * clogp - 0.0062 * mw + 0.066 * rotb - 0.74 * ap


def _pains(mol) -> dict:
    """PAINS / frequent-hitter screen. Returns match flag + any alert descriptions."""
    try:
        from rdkit.Chem import FilterCatalog
        params = FilterCatalog.FilterCatalogParams()
        params.AddCatalog(FilterCatalog.FilterCatalogParams.FilterCatalogs.PAINS)
        catalog = FilterCatalog.FilterCatalog(params)
        if catalog.HasMatch(mol):
            entries = [e.GetDescription() for e in catalog.GetMatches(mol)]
            return {"match": True, "alerts": entries}
        return {"match": False, "alerts": []}
    except Exception as exc:
        return {"match": None, "error": str(exc)}


def _ligand_efficiency(desc: dict, pic50_values: dict) -> list[dict]:
    """
    LE   = 1.37 * pIC50 / HAC          (kcal/mol per heavy atom, 1.37 = 2.303*RT at 298K)
    LLE  = pIC50 - cLogP               (lipophilic efficiency / LipE)
    LELP = cLogP / LE
    pic50_values: {context_label: pIC50}
    """
    hac = desc.get("heavy_atom_count")
    clogp = desc.get("clogp_crippen")
    rows = []
    for label, pic50 in pic50_values.items():
        try:
            pic50 = float(pic50)
        except (TypeError, ValueError):
            continue
        le = 1.37 * pic50 / hac if hac else None
        lle = pic50 - clogp if clogp is not None else None
        lelp = (clogp / le) if (le and clogp is not None) else None
        rows.append({
            "context": label,
            "pIC50": round(pic50, 2),
            "LE": round(le, 2) if le is not None else None,
            "LLE_LipE": round(lle, 2) if lle is not None else None,
            "LELP": round(lelp, 1) if lelp is not None else None,
        })
    return rows


# --------------------------------------------------------------------------- #
# SMILES resolution fallback (only used if not threaded from PubChem)
# --------------------------------------------------------------------------- #
async def _resolve_smiles(cid, name: str) -> Optional[str]:
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            if not cid and name:
                r = await retryable_get(
                    client, f"{PUBCHEM}/compound/name/{name}/cids/JSON", timeout=8
                )
                cids = r.json().get("IdentifierList", {}).get("CID", [])
                cid = str(cids[0]) if cids else None
            if not cid:
                return None
            r = await retryable_get(
                client,
                f"{PUBCHEM}/compound/cid/{cid}/property/SMILES/JSON",
                timeout=8,
            )
            props = r.json().get("PropertyTable", {}).get("Properties", [{}])[0]
            return props.get("SMILES") or props.get("CanonicalSMILES")
    except Exception:
        return None
