"""AlphaFold DB connector — AI-predicted protein structures.

Image / 3D policy: the predicted-model coordinate URLs (pdb/cif), the PAE image, and the
interactive viewer URL are returned ONLY when params["include_images"] is true. By
default the connector returns text metadata (accession, pLDDT, length, organism) so the
AlphaFold structure is never rendered unless the user explicitly asks for it.
"""
import httpx
from connectors.utils import retryable_get

BASE = "https://alphafold.ebi.ac.uk/api"


async def fetch(entity_ids: dict, params: dict) -> dict:
    """
    Fetches AlphaFold predicted structure metadata for the target protein.
    params:
      include_images: bool (default False) — gate model/cif/PAE/viewer URLs.
    Returns:
      {"accession": str, "entry_id": str, "plddt_global": float | None,
       "sequence_length": int | None, "organism": str, "available": bool}
      plus (only if include_images) model_url / cif_url / pae_image_url / viewer_url.
    """
    accession = entity_ids.get("target_uniprot")
    if not accession:
        return {}
    include_images = bool(params.get("include_images", False))

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            r = await retryable_get(client, f"{BASE}/prediction/{accession}", timeout=10)
            if r.status_code == 404:
                return {"accession": accession, "available": False}

            data = r.json()
            if not data:
                return {"accession": accession, "available": False}

            entry = data[0] if isinstance(data, list) else data
            out = {
                "accession": accession,
                "entry_id": entry.get("entryId", f"AF-{accession}-F1"),
                "plddt_global": entry.get("globalMetricValue"),
                "sequence_length": entry.get("seqLength"),
                "organism": entry.get("organismScientificName", ""),
                "available": True,
            }
            if include_images:
                out["model_url"] = entry.get(
                    "pdbUrl", f"https://alphafold.ebi.ac.uk/files/AF-{accession}-F1-model_v4.pdb"
                )
                out["cif_url"] = entry.get("cifUrl", "")
                out["pae_image_url"] = entry.get("paeImageUrl", "")
                out["viewer_url"] = f"https://alphafold.ebi.ac.uk/entry/{accession}"
            return out
    except Exception as e:
        return {"accession": accession, "error": str(e), "available": False}
