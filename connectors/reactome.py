"""Reactome connector — biological pathways + signaling. Cell / molecular biologist."""
import httpx

BASE = "https://reactome.org/ContentService"


async def fetch(entity_ids: dict, params: dict) -> dict:
    """
    Fetches pathways the target protein participates in.
    Returns:
      {"pathways": [{"stable_id": str, "display_name": str, "species": str}]}
    """
    uniprot_id = entity_ids.get("target_uniprot")
    target = entity_ids.get("target", "")

    if not uniprot_id:
        return {"pathways": []}

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            pathways = await _fetch_pathways(client, uniprot_id)

            # If few results, also search by gene name
            if len(pathways) < 3 and target:
                extra = await _search_pathways(client, target)
                seen = {p["stable_id"] for p in pathways}
                for p in extra:
                    if p["stable_id"] not in seen:
                        pathways.append(p)

            return {"pathways": pathways[:10], "uniprot_id": uniprot_id}
    except Exception as e:
        return {"pathways": [], "error": str(e)}


async def _fetch_pathways(client: httpx.AsyncClient, uniprot_id: str) -> list[dict]:
    """Map UniProt ID → pathways via Reactome mapping service."""
    try:
        r = await client.get(
            f"{BASE}/data/mapping/UniProt/{uniprot_id}/pathways",
            timeout=10,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        return [
            {
                "stable_id": p.get("stId", ""),
                "display_name": p.get("displayName", ""),
                "species": p.get("speciesName", ""),
            }
            for p in (data if isinstance(data, list) else [])
        ]
    except Exception:
        return []


async def _search_pathways(client: httpx.AsyncClient, query: str) -> list[dict]:
    """Full-text search for pathways by gene/drug name."""
    try:
        r = await client.get(
            f"{BASE}/search/query",
            params={"query": query, "types": "Pathway", "species": "Homo sapiens"},
            timeout=10,
        )
        if r.status_code != 200:
            return []
        results = r.json().get("results", [])
        entries = []
        for group in results:
            for entry in group.get("entries", [])[:4]:
                entries.append({
                    "stable_id": entry.get("stId", ""),
                    "display_name": entry.get("name", ""),
                    "species": "Homo sapiens",
                })
        return entries
    except Exception:
        return []
