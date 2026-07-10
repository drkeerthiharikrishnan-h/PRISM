"""STRING connector — protein-protein interaction partners.

Image policy: the network diagram URLs (PNG/SVG) and the interactive STRING viewer URL
are returned ONLY when params["include_images"] is true. By default the connector
returns the scored partner list as text so no network diagram is rendered unless the
user explicitly asks for it.
"""
from urllib.parse import urlencode

import httpx

from connectors.utils import retryable_get

BASE = "https://string-db.org/api"
NETWORK_PAGE = "https://string-db.org/cgi/network"


def _network_urls(symbol: str, species: int, add_nodes: int) -> dict:
    query = {
        "identifiers": symbol,
        "species": species,
        "add_white_nodes": add_nodes,
        "network_flavor": "confidence",
    }
    qs = urlencode(query)
    return {
        "network_image_url": f"{BASE}/image/network?{qs}",
        "network_svg_url": f"{BASE}/svg/network?{qs}",
        "viewer_url": f"{NETWORK_PAGE}?{urlencode({'identifiers': symbol, 'species': species})}",
    }


async def fetch(entity_ids: dict, params: dict) -> dict:
    """Return STRING interaction partners for the target (network visuals gated)."""
    symbol = entity_ids.get("target", "")
    if not symbol:
        return {"partners": []}
    species = int(params.get("species", 9606))
    limit = int(params.get("limit", 10))
    min_score = float(params.get("min_score", 0.4))
    include_images = bool(params.get("include_images", False))

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await retryable_get(
                client,
                f"{BASE}/json/interaction_partners",
                params={"identifiers": symbol, "species": species, "limit": limit},
                timeout=12,
            )
            partners = []
            for row in response.json():
                score = float(row.get("score", 0) or 0)
                if score < min_score:
                    continue
                partners.append(
                    {
                        "partner": row.get("preferredName_B", ""),
                        "score": round(score, 3),
                        "experimental": round(float(row.get("escore", 0) or 0), 3),
                        "database": round(float(row.get("dscore", 0) or 0), 3),
                        "textmining": round(float(row.get("tscore", 0) or 0), 3),
                    }
                )
            out = {"query": symbol, "partners": partners}
            if include_images:
                out.update(_network_urls(symbol, species, max(len(partners), limit)))
            return out
    except Exception as exc:
        return {"partners": [], "error": str(exc)}
