"""STRING connector — protein-protein interaction network."""
import httpx
from connectors.utils import retryable_get

BASE = "https://string-db.org/api"


async def fetch(entity_ids: dict, params: dict) -> dict:
    target = entity_ids.get("target", "")
    if not target:
        return {}
    species = params.get("species", 9606)
    limit = min(params.get("limit", 10), 10)
    min_score = params.get("min_score", 0.4)
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            r = await retryable_get(
                client, f"{BASE}/json/interaction_partners",
                params={
                    "identifier": target,
                    "species": species,
                    "limit": limit,
                    "required_score": int(min_score * 1000),
                },
                timeout=10,
            )
            if r.status_code != 200:
                return {}
            interactions = r.json()
            partners = [
                {
                    "partner": i.get("preferredName_B", ""),
                    "score": round(i.get("score", 0) / 1000, 3),
                    "experimental": round(i.get("escore", 0) / 1000, 3),
                    "database": round(i.get("dscore", 0) / 1000, 3),
                    "textmining": round(i.get("tscore", 0) / 1000, 3),
                }
                for i in interactions[:limit]
            ]
            network_image_url = (
                f"https://string-db.org/api/image/network"
                f"?identifier={target}&species={species}&network_type=functional"
            )
            return {
                "partners": partners,
                "network_image_url": network_image_url,
                "viewer_url": f"https://string-db.org/network/{target}%0d{species}",
            }
    except Exception as e:
        return {"error": str(e)}
