"""InterPro connector — protein family and domain architecture."""
import httpx

from connectors.utils import retryable_get

BASE = "https://www.ebi.ac.uk/interpro/api"


async def fetch(entity_ids: dict, params: dict) -> dict:
    """Return curated InterPro entries for the target UniProt accession."""
    accession = entity_ids.get("target_uniprot")
    if not accession:
        return {"entries": []}
    limit = int(params.get("limit", 12))

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await retryable_get(
                client,
                f"{BASE}/entry/interpro/protein/uniprot/{accession}/",
                timeout=12,
            )
            if response.status_code != 200:
                return {"accession": accession, "entries": []}
            data = response.json()
            entries = []
            for row in data.get("results", [])[:limit]:
                metadata = row.get("metadata", {})
                entries.append(
                    {
                        "interpro_id": metadata.get("accession", ""),
                        "name": metadata.get("name", ""),
                        "type": metadata.get("type", ""),
                    }
                )
            return {
                "accession": accession,
                "entry_count": data.get("count", len(entries)),
                "entries": entries,
            }
    except Exception as exc:
        return {"accession": accession, "entries": [], "error": str(exc)}
