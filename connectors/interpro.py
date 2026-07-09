"""InterPro connector — protein family & domain architecture. EBI InterPro API."""
import httpx
from connectors.utils import retryable_get

BASE = "https://www.ebi.ac.uk/interpro/api"


async def fetch(entity_ids: dict, params: dict) -> dict:
    accession = entity_ids.get("target_uniprot")
    if not accession:
        return {}
    limit = min(params.get("limit", 12), 12)
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            r = await retryable_get(
                client, f"{BASE}/entry/interpro/protein/UniProt/{accession}/",
                params={"page_size": limit, "format": "json"},
                timeout=10,
            )
            if r.status_code != 200:
                return {}
            data = r.json()
            entries = []
            for item in data.get("results", []):
                meta = item.get("metadata", {})
                entries.append({
                    "interpro_id": meta.get("accession", ""),
                    "name": meta.get("name", {}).get("name", ""),
                    "type": meta.get("type", ""),
                })
            return {"entry_count": data.get("count", len(entries)), "entries": entries}
    except Exception as e:
        return {"error": str(e)}
