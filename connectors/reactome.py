"""Reactome connector — biological pathways + signaling. Cell / molecular biologist.

Image policy: pathway diagram PNGs and the interactive PathwayBrowser URL are returned
ONLY when params["include_images"] is true. By default the connector returns pathway
identifiers and names as text so no diagram is rendered unless explicitly requested.
"""
import httpx
from connectors.utils import retryable_get

BASE = "https://reactome.org/ContentService"

DIAGRAM_EXPORTER = BASE + "/exporter/diagram/{stid}.png?quality=7"
PATHWAY_BROWSER = "https://reactome.org/PathwayBrowser/#/{stid}"


def _visual_urls(stid: str) -> dict:
    if not stid:
        return {"diagram_url": "", "viewer_url": ""}
    return {
        "diagram_url": DIAGRAM_EXPORTER.format(stid=stid),
        "viewer_url": PATHWAY_BROWSER.format(stid=stid),
    }


async def fetch(entity_ids: dict, params: dict) -> dict:
    """
    Fetches pathways the target protein participates in.
    params:
      include_images: bool (default False) — gate diagram/viewer URLs per pathway.
    Returns:
      {"pathways": [{"stable_id": str, "display_name": str, "species": str}]}
    """
    uniprot_id = entity_ids.get("target_uniprot")
    target = entity_ids.get("target", "")
    include_images = bool(params.get("include_images", False))

    if not uniprot_id:
        return {"pathways": []}

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            pathways = await _fetch_pathways(client, uniprot_id, include_images)

            # If few results, also search by gene name
            if len(pathways) < 3 and target:
                extra = await _search_pathways(client, target, include_images)
                seen = {p["stable_id"] for p in pathways}
                for p in extra:
                    if p["stable_id"] not in seen:
                        pathways.append(p)

            return {"pathways": pathways[:10], "uniprot_id": uniprot_id}
    except Exception as e:
        return {"pathways": [], "error": str(e)}


async def _fetch_pathways(client: httpx.AsyncClient, uniprot_id: str, include_images: bool) -> list[dict]:
    """Map UniProt ID → pathways via Reactome mapping service."""
    try:
        r = await retryable_get(
            client, f"{BASE}/data/mapping/UniProt/{uniprot_id}/pathways",
            timeout=10,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        out = []
        for p in (data if isinstance(data, list) else []):
            row = {
                "stable_id": p.get("stId", ""),
                "display_name": p.get("displayName", ""),
                "species": p.get("speciesName", ""),
            }
            if include_images:
                row.update(_visual_urls(p.get("stId", "")))
            out.append(row)
        return out
    except Exception:
        return []


async def _search_pathways(client: httpx.AsyncClient, query: str, include_images: bool) -> list[dict]:
    """Full-text search for pathways by gene/drug name."""
    try:
        r = await retryable_get(
            client, f"{BASE}/search/query",
            params={"query": query, "types": "Pathway", "species": "Homo sapiens"},
            timeout=10,
        )
        if r.status_code != 200:
            return []
        results = r.json().get("results", [])
        entries = []
        for group in results:
            for entry in group.get("entries", [])[:4]:
                row = {
                    "stable_id": entry.get("stId", ""),
                    "display_name": entry.get("name", ""),
                    "species": "Homo sapiens",
                }
                if include_images:
                    row.update(_visual_urls(entry.get("stId", "")))
                entries.append(row)
        return entries
    except Exception:
        return []
