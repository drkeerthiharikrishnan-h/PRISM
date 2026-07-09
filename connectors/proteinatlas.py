"""Human Protein Atlas connector — pathology and microscopy images."""
import httpx
from connectors.utils import retryable_get

BASE = "https://www.proteinatlas.org"


async def fetch(entity_ids: dict, params: dict) -> dict:
    target = entity_ids.get("target", "")
    ensembl_id = entity_ids.get("target_ensembl", "")
    image_type = params.get("image_type", "all")
    limit = min(params.get("limit", 6), 6)

    if not ensembl_id and not target:
        return {}

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            if not ensembl_id:
                ensembl_id = await _resolve_ensembl(client, target)
            if not ensembl_id:
                return {"error": f"Could not resolve Ensembl ID for {target}"}

            r = await retryable_get(
                client, f"{BASE}/{ensembl_id}.json",
                timeout=12,
            )
            if r.status_code != 200:
                return {}

            data = r.json()
            gene = data.get("gene", target)

            pathology_images = []
            microscopy_images = []

            for entry in data.get("tissue", []):
                tissue = entry.get("tissue", "")
                for img in entry.get("images", [])[:2]:
                    pathology_images.append({
                        "url": img.get("highres_url", img.get("thumbnail_url", "")),
                        "tissue": tissue,
                        "assay": img.get("assay_type", "IHC"),
                        "antibody": img.get("antibody_id", ""),
                    })

            for entry in data.get("subcell_location", []):
                location = entry.get("location", "")
                for img in entry.get("images", [])[:2]:
                    microscopy_images.append({
                        "url": img.get("highres_url", img.get("thumbnail_url", "")),
                        "locations": location,
                        "assay": "ICC/IF",
                    })

            return {
                "gene": gene,
                "ensembl_id": ensembl_id,
                "pathology_images": pathology_images[:limit],
                "microscopy_images": microscopy_images[:limit],
                "pathology_total": len(pathology_images),
                "microscopy_total": len(microscopy_images),
            }
    except Exception as e:
        return {"error": str(e)}


async def _resolve_ensembl(client: httpx.AsyncClient, gene_symbol: str) -> str:
    try:
        r = await retryable_get(
            client, f"{BASE}/search?q={gene_symbol}&format=json",
            timeout=8,
        )
        if r.status_code == 200:
            results = r.json()
            if results:
                return results[0].get("ensembl_id", "")
    except Exception:
        pass
    return ""
