"""AlphaFold DB connector — AI-predicted protein structures. Computational biologist."""
import httpx
from connectors.utils import retryable_get

BASE = "https://alphafold.ebi.ac.uk/api"


async def fetch(entity_ids: dict, params: dict) -> dict:
    """
    Fetches AlphaFold predicted structure metadata for the target protein.
    Returns:
      {"accession": str, "entry_id": str, "model_url": str,
       "plddt_global": float | None, "sequence_length": int | None,
       "organism": str}
    """
    accession = entity_ids.get("target_uniprot")
    if not accession:
        return {}

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            r = await retryable_get(client, f"{BASE}/prediction/{accession}", timeout=10)
            if r.status_code == 404:
                return {"accession": accession, "available": False}

            data = r.json()
            if not data:
                return {"accession": accession, "available": False}

            entry = data[0] if isinstance(data, list) else data
            return {
                "accession": accession,
                "entry_id": entry.get("entryId", f"AF-{accession}-F1"),
                "model_url": entry.get("pdbUrl", f"https://alphafold.ebi.ac.uk/files/AF-{accession}-F1-model_v4.pdb"),
                "cif_url": entry.get("cifUrl", ""),
                "plddt_global": entry.get("globalMetricValue"),
                "sequence_length": entry.get("seqLength"),
                "organism": entry.get("organismScientificName", ""),
                "available": True,
            }
    except Exception as e:
        return {"accession": accession, "error": str(e), "available": False}
