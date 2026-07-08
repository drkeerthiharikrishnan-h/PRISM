"""PDB/RCSB connector — 3D structures. Used by chemist + comp biologist."""
import httpx
from connectors.utils import retryable_get, retryable_post

SEARCH_URL = "https://search.rcsb.org/rcsbsearch/v2/query"
ENTRY_URL = "https://data.rcsb.org/rest/v1/core/entry"


async def fetch(entity_ids: dict, params: dict) -> dict:
    """
    params:
      query_type: "ligand_search" | "all_structures"
    Returns:
      {"structures": [{"pdb_id": str, "title": str, "resolution": float, "method": str}]}
    """
    entity = entity_ids.get("entity", "")
    target_uniprot = entity_ids.get("target_uniprot")

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            pdb_ids = await _search_structures(client, entity, target_uniprot)
            if not pdb_ids:
                return {"structures": []}

            details = []
            for pdb_id in pdb_ids[:5]:
                detail = await _fetch_entry(client, pdb_id)
                if detail:
                    details.append(detail)

            return {"structures": details}
    except Exception as e:
        return {"structures": [], "error": str(e)}


async def _search_structures(client: httpx.AsyncClient, entity: str, uniprot_id: str | None) -> list[str]:
    """Search RCSB for structures containing the entity as a ligand."""
    query: dict = {
        "query": {
            "type": "terminal",
            "service": "full_text",
            "parameters": {"value": entity},
        },
        "return_type": "entry",
        "request_options": {"paginate": {"start": 0, "rows": 8}},
    }
    # If we have UniProt, prefer macromolecule search
    if uniprot_id:
        query = {
            "query": {
                "type": "terminal",
                "service": "sequence",
                "parameters": {
                    "target": "pdb_protein_sequence",
                    "value": uniprot_id,
                    "identity_cutoff": 0.9,
                    "evalue_cutoff": 1,
                },
            },
            "return_type": "entry",
            "request_options": {"paginate": {"start": 0, "rows": 8}},
        }

    r = await retryable_post(client, SEARCH_URL, json=query, timeout=12)
    if r.status_code != 200:
        # Fallback to text search
        fallback = {
            "query": {
                "type": "terminal",
                "service": "full_text",
                "parameters": {"value": f"{entity}"},
            },
            "return_type": "entry",
            "request_options": {"paginate": {"start": 0, "rows": 8}},
        }
        r = await retryable_post(client, SEARCH_URL, json=fallback, timeout=12)

    data = r.json()
    return [hit["identifier"] for hit in data.get("result_set", [])]


async def _fetch_entry(client: httpx.AsyncClient, pdb_id: str) -> dict | None:
    """Fetch title, resolution, and experimental method for a PDB entry."""
    try:
        r = await retryable_get(client, f"{ENTRY_URL}/{pdb_id}", timeout=8)
        d = r.json()
        struct = d.get("struct", {})
        refine = d.get("refine", [{}])
        exptl = d.get("exptl", [{}])
        resolution = None
        if refine and isinstance(refine, list):
            resolution = refine[0].get("ls_d_res_high")
        return {
            "pdb_id": pdb_id,
            "title": struct.get("title", ""),
            "resolution_angstrom": resolution,
            "method": exptl[0].get("method", "") if exptl else "",
        }
    except Exception:
        return None
