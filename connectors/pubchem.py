"""PubChem connector — scaffold / SMILES / molecular properties. Medicinal chemist."""
from typing import Optional
import httpx
from connectors.utils import retryable_get

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
            r = await retryable_get(
                client, f"{BASE}/compound/cid/{cid}/property/"
                "SMILES,MolecularFormula,MolecularWeight,IUPACName/JSON",
                timeout=8,
            )
            props = r.json().get("PropertyTable", {}).get("Properties", [{}])[0]
            # PubChem returns "SMILES" (was "CanonicalSMILES" in older API versions)
            smiles = props.get("SMILES") or props.get("CanonicalSMILES", "")
            return {
                "cid": cid,
                "canonical_smiles": smiles[:200],
                "molecular_formula": props.get("MolecularFormula", ""),
                "molecular_weight": props.get("MolecularWeight"),
                "iupac_name": props.get("IUPACName", "")[:150],
            }
    except Exception as e:
        return {"cid": cid, "error": str(e)}


async def _lookup_cid(name: str) -> Optional[str]:
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            r = await retryable_get(
                client, f"{BASE}/compound/name/{name}/cids/JSON",
                timeout=8,
            )
            cids = r.json().get("IdentifierList", {}).get("CID", [])
            return str(cids[0]) if cids else None
    except Exception:
        return None
