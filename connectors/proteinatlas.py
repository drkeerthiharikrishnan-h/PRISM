"""Human Protein Atlas connector — pathology and microscopy images.

Image policy: HPA's whole purpose is image retrieval, so this connector is the clearest
case for gating. When params["include_images"] is FALSE (the default) it returns only
COUNTS and tissue/location metadata (how many pathology / microscopy images exist, which
tissues, subcellular locations) and NO image URLs — nothing renders. When
params["include_images"] is TRUE it returns the actual image URL lists. This lets a
persona report "IHC images available for N tissues" without pulling the pictures unless
the user explicitly asks to see microscopy.
"""
from typing import Optional
import xml.etree.ElementTree as ET

import httpx

from connectors.utils import retryable_get

SEARCH = "https://www.proteinatlas.org/api/search_download.php"


async def fetch(entity_ids: dict, params: dict) -> dict:
    """Return HPA pathology/microscopy image metadata (URLs only when gated on)."""
    ensembl = entity_ids.get("target_ensembl")
    symbol = entity_ids.get("target", "")
    image_type = params.get("image_type", "all")
    include_cancer = params.get("include_cancer", True)
    include_images = bool(params.get("include_images", False))
    limit = int(params.get("limit", 6))

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            if not ensembl and symbol:
                ensembl = await _resolve_ensembl(client, symbol)
            if not ensembl:
                return {
                    "pathology_images": [],
                    "microscopy_images": [],
                    "note": "no Ensembl gene id resolved",
                }

            response = await retryable_get(client, f"https://www.proteinatlas.org/{ensembl}.xml", timeout=40)
            entry = ET.fromstring(response.content).find("entry")
            if entry is None:
                return {"pathology_images": [], "microscopy_images": [], "ensembl_id": ensembl}
            gene = entry.findtext("name") or symbol

            pathology_images = []
            microscopy_images = []
            if image_type in ("pathology", "all"):
                for antibody in entry.findall("antibody"):
                    antibody_id = antibody.get("id")
                    for tissue_expression in antibody.findall("tissueExpression"):
                        assay = tissue_expression.get("assayType")
                        if assay == "cancer" and not include_cancer:
                            continue
                        for data in tissue_expression.findall("data"):
                            tissue = data.findtext("tissue")
                            for image in data.findall(".//image"):
                                url = image.findtext("imageUrl")
                                if not url:
                                    continue
                                if not url.lower().endswith((".jpg", ".jpeg", ".png")):
                                    url += ".jpg"
                                pathology_images.append(
                                    {
                                        "url": url,
                                        "tissue": tissue,
                                        "assay": "IHC_" + assay,
                                        "antibody": antibody_id,
                                    }
                                )

            if image_type in ("microscopy", "all"):
                for cell_expression in entry.findall("cellExpression"):
                    locations = [location.text for location in cell_expression.findall("data/location") if location.text]
                    for image in cell_expression.findall(".//image"):
                        url = image.findtext("imageUrl")
                        if url:
                            microscopy_images.append({"url": url, "locations": locations, "assay": "ICC/IF"})

            out = {
                "gene": gene,
                "ensembl_id": ensembl,
                "pathology_total": len(pathology_images),
                "microscopy_total": len(microscopy_images),
            }
            if include_images:
                out["pathology_images"] = pathology_images[:limit]
                out["microscopy_images"] = microscopy_images[:limit]
            else:
                # Report availability + context WITHOUT image URLs so nothing renders.
                out["pathology_images"] = []
                out["microscopy_images"] = []
                out["pathology_tissues"] = sorted({p["tissue"] for p in pathology_images if p.get("tissue")})[:limit]
                subcell = sorted({loc for m in microscopy_images for loc in m.get("locations", [])})
                out["microscopy_locations"] = subcell[:limit]
                out["note"] = "image URLs withheld (include_images=false); set include_images=true to render"
            return out
    except Exception as exc:
        return {"pathology_images": [], "microscopy_images": [], "error": str(exc)}


async def _resolve_ensembl(client: httpx.AsyncClient, symbol: str) -> Optional[str]:
    response = await retryable_get(
        client,
        SEARCH,
        params={"search": symbol, "format": "json", "columns": "g,eg", "compress": "no"},
        timeout=20,
    )
    rows = response.json()
    for row in rows:
        if (row.get("Gene") or "").upper() == symbol.upper():
            return row.get("Ensembl")
    return rows[0].get("Ensembl") if rows else None
