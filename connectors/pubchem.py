"""PubChem connector — scaffold / SMILES / molecular properties. Medicinal chemist."""
import httpx

BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"


async def fetch(entity_ids: dict, params: dict) -> dict:
    """
    params:
      query_type: "scaffold"  (default)
    Returns:
      {"cid": str, "canonical_smiles": str, "molecular_formula": str,
       "molecular_weight": float, "iupac_name": str}
    """
    cid = entity_ids.get("drug_pubchem")
    entity = entity_ids.get("entity", "")

    if not cid:
        cid = await _lookup_cid(entity)
    if not cid:
        return {}

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            r = await client.get(
                f"{BASE}/compound/cid/{cid}/property/"
                "CanonicalSMILES,MolecularFormula,MolecularWeight,IUPACName/JSON",
                timeout=8,
            )
            props = r.json().get("PropertyTable", {}).get("Properties", [{}])[0]
            return {
                "cid": cid,
                "canonical_smiles": props.get("CanonicalSMILES", ""),
                "molecular_formula": props.get("MolecularFormula", ""),
                "molecular_weight": props.get("MolecularWeight"),
                "iupac_name": props.get("IUPACName", ""),
            }
    except Exception as e:
        return {"cid": cid, "error": str(e)}


async def _lookup_cid(name: str) -> str | None:
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            r = await client.get(
                f"{BASE}/compound/name/{name}/cids/JSON",
                timeout=8,
            )
            cids = r.json().get("IdentifierList", {}).get("CID", [])
            return str(cids[0]) if cids else None
    except Exception:
        return None
