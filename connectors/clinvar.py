"""ClinVar connector — resistance variants + clinical significance. Pathologist."""
import os
import httpx

NCBI_KEY = os.getenv("NCBI_API_KEY", "")
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


async def fetch(entity_ids: dict, params: dict) -> dict:
    """
    Searches ClinVar for variants in the target gene associated with drug resistance.
    Returns:
      {"variants": [{"variant_id": str, "title": str, "clinical_significance": str,
                     "condition": str, "review_status": str}]}
    """
    target = entity_ids.get("target", "")
    entity = entity_ids.get("entity", "")

    if not target:
        return {"variants": []}

    term = f"{target}[gene] AND ({entity} resistance OR drug resistance OR pathogenic)"
    base_params = {
        "db": "clinvar",
        "term": term,
        "retmax": 8,
        "retmode": "json",
    }
    if NCBI_KEY:
        base_params["api_key"] = NCBI_KEY

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            # Search
            r = await client.get(f"{BASE}/esearch.fcgi", params=base_params, timeout=10)
            ids = r.json().get("esearchresult", {}).get("idlist", [])
            if not ids:
                return {"variants": [], "gene": target}

            # Summary
            r2 = await client.get(
                f"{BASE}/esummary.fcgi",
                params={
                    "db": "clinvar",
                    "id": ",".join(ids[:8]),
                    "retmode": "json",
                    **({"api_key": NCBI_KEY} if NCBI_KEY else {}),
                },
                timeout=10,
            )
            result_data = r2.json().get("result", {})

            variants = []
            for vid in ids[:8]:
                v = result_data.get(str(vid), {})
                if not v or vid == "uids":
                    continue
                germline = v.get("germline_classification", {})
                variants.append({
                    "variant_id": vid,
                    "title": v.get("title", ""),
                    "clinical_significance": germline.get("description", ""),
                    "condition": _extract_condition(v),
                    "review_status": germline.get("review_status", ""),
                })

            return {"variants": variants, "gene": target}

    except Exception as e:
        return {"variants": [], "error": str(e)}


def _extract_condition(variant_data: dict) -> str:
    """Extract primary condition name from ClinVar variant summary."""
    traits = variant_data.get("trait_set", [])
    if traits and isinstance(traits, list):
        names = traits[0].get("trait_name", "")
        return names[:120] if names else ""
    return ""
