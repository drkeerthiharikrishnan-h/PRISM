"""ChEMBL connector — potency data (chemist) + bioactivity dataset (comp biologist)."""
import httpx

BASE = "https://www.ebi.ac.uk/chembl/api/data"


async def fetch(entity_ids: dict, params: dict) -> dict:
    """
    params:
      query_type: "activity" | "dataset"
      standard_types: list[str]  (for activity)
      limit: int                 (for dataset, default 20)
    Returns:
      activity → {"activities": [...], "count": int}
      dataset  → {"dataset_count": int, "sample": [...]}
    """
    query_type = params.get("query_type", "activity")
    drug_chembl = entity_ids.get("drug_chembl")
    target_chembl = entity_ids.get("target_chembl")

    if not drug_chembl and not target_chembl:
        return {}

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            if query_type == "activity":
                return await _fetch_activity(client, drug_chembl, target_chembl, params)
            else:
                return await _fetch_dataset(client, target_chembl, params)
    except Exception as e:
        return {"error": str(e)}


async def _fetch_activity(client, drug_chembl, target_chembl, params) -> dict:
    std_types = params.get("standard_types", ["IC50", "Ki", "Kd"])
    req_params = {
        "format": "json",
        "limit": 10,
        "standard_type__in": ",".join(std_types),
    }
    if drug_chembl:
        req_params["molecule_chembl_id"] = drug_chembl
    if target_chembl:
        req_params["target_chembl_id"] = target_chembl

    r = await client.get(f"{BASE}/activity.json", params=req_params, timeout=10)
    data = r.json()
    activities = data.get("activities", [])

    cleaned = [
        {
            "molecule_chembl_id": a.get("molecule_chembl_id"),
            "standard_type": a.get("standard_type"),
            "standard_value": a.get("standard_value"),
            "standard_units": a.get("standard_units"),
            "assay_description": (a.get("assay_description") or "")[:120],
        }
        for a in activities
        if a.get("standard_value")
    ]
    return {"activities": cleaned, "count": data.get("page_meta", {}).get("total_count", len(cleaned))}


async def _fetch_dataset(client, target_chembl, params) -> dict:
    if not target_chembl:
        return {}
    limit = params.get("limit", 20)
    r = await client.get(
        f"{BASE}/activity.json",
        params={"target_chembl_id": target_chembl, "format": "json", "limit": limit},
        timeout=10,
    )
    data = r.json()
    total = data.get("page_meta", {}).get("total_count", 0)
    sample = [
        {
            "molecule_chembl_id": a.get("molecule_chembl_id"),
            "standard_type": a.get("standard_type"),
            "standard_value": a.get("standard_value"),
            "standard_units": a.get("standard_units"),
        }
        for a in data.get("activities", [])[:5]
    ]
    return {"dataset_count": total, "sample": sample, "target_chembl_id": target_chembl}
