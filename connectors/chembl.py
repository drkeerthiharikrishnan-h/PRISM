"""ChEMBL connector — potency (chemist), bioactivity dataset (comp bio),
and compound-wide selectivity profile across targets (cell/molecular biologist).

Query modes (params["query_type"]):
  "activity"             (default) — activity rows for a compound and/or target
  "dataset"                        — target-centric activity sample + total count
  "selectivity_profile"            — every IC50/Ki/Kd for a compound aggregated by
                                     target, with computed pAct, target_type
                                     (SINGLE PROTEIN vs CELL-LINE), and an on/off-target
                                     class hint. This is the data behind the
                                     molecular-biologist selectivity & potency table.

Image policy: the 2D structure SVG depiction is returned ONLY when
params["include_images"] is true.
"""
import math

import httpx

from connectors.utils import retryable_get

BASE = "https://www.ebi.ac.uk/chembl/api/data"


def structure_image_url(molecule_chembl_id: str) -> str:
    """Directly renderable 2D depiction for a ChEMBL molecule id."""
    return f"{BASE}/image/{molecule_chembl_id}.svg"


async def fetch(entity_ids: dict, params: dict) -> dict:
    """
    params:
      query_type: "activity" | "dataset" | "selectivity_profile"
      standard_types: list[str]  (activity / selectivity)
      limit: int
      include_images: bool (default False)
    """
    query_type = params.get("query_type", "activity")
    drug_chembl = entity_ids.get("drug_chembl")
    target_chembl = entity_ids.get("target_chembl")
    include_images = bool(params.get("include_images", False))

    if not drug_chembl and not target_chembl:
        return {}

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            if query_type == "selectivity_profile":
                return await _fetch_selectivity(client, drug_chembl, target_chembl, params, include_images)
            if query_type == "activity":
                return await _fetch_activity(client, drug_chembl, target_chembl, params, include_images)
            return await _fetch_dataset(client, target_chembl, params, include_images)
    except Exception as e:
        return {"error": str(e)}


# --------------------------------------------------------------------------- #
# Selectivity profile
# --------------------------------------------------------------------------- #
async def _fetch_selectivity(client, drug_chembl, target_chembl, params, include_images) -> dict:
    """Aggregate all IC50/Ki/Kd for a compound across targets → pAct-ranked profile."""
    if not drug_chembl:
        return {"error": "selectivity_profile requires drug_chembl", "targets": []}

    std_types = params.get("standard_types", ["IC50", "Ki", "Kd"])
    organism = params.get("organism", "Homo sapiens")
    max_records = int(params.get("max_records", 1000))

    # Page through activity records that carry a pchembl_value.
    groups: dict = {}
    offset = 0
    page = 200
    while offset < max_records:
        req = {
            "molecule_chembl_id": drug_chembl,
            "format": "json",
            "limit": page,
            "offset": offset,
            "standard_type__in": ",".join(std_types),
        }
        if organism:
            req["target_organism"] = organism
        r = await retryable_get(client, f"{BASE}/activity.json", params=req, timeout=30)
        acts = r.json().get("activities", [])
        if not acts:
            break
        for a in acts:
            pv = a.get("pchembl_value")
            if not pv:
                continue
            tid = a.get("target_chembl_id")
            if not tid:
                continue
            g = groups.setdefault(tid, {
                "target_chembl_id": tid,
                "target_pref_name": a.get("target_pref_name", ""),
                "target_organism": a.get("target_organism", ""),
                "pact_values": [],
                "best": None,
            })
            pvf = float(pv)
            g["pact_values"].append(pvf)
            # Keep the record that gives the strongest (max) pAct as representative.
            if g["best"] is None or pvf > g["best"]["pchembl_value"]:
                g["best"] = {
                    "pchembl_value": pvf,
                    "standard_type": a.get("standard_type"),
                    "standard_value": a.get("standard_value"),
                    "standard_units": a.get("standard_units"),
                    "standard_relation": a.get("standard_relation"),
                    "assay_variant_mutation": a.get("assay_variant_mutation"),
                }
        offset += page
        if len(acts) < page:
            break

    if not groups:
        return {"molecule_chembl_id": drug_chembl, "targets": [], "note": "no pchembl-valued activities"}

    # Fetch target_type for all grouped targets in one batched call.
    target_types = await _fetch_target_types(client, list(groups.keys()))

    rows = []
    for tid, g in groups.items():
        vals = g["pact_values"]
        best = g["best"]
        ttype = target_types.get(tid, "")
        rows.append({
            "target_chembl_id": tid,
            "target_pref_name": g["target_pref_name"],
            "target_organism": g["target_organism"],
            "target_type": ttype,
            "best_pact": round(max(vals), 2),
            "median_pact": round(sorted(vals)[len(vals) // 2], 2),
            "n_measurements": len(vals),
            "representative_metric": best["standard_type"],
            "representative_value": best["standard_value"],
            "representative_units": best["standard_units"],
            "representative_relation": best["standard_relation"],
            "assay_variant_mutation": best["assay_variant_mutation"],
            "class_hint": _class_hint(tid, ttype, target_chembl),
        })
    rows.sort(key=lambda x: x["best_pact"], reverse=True)

    out = {
        "molecule_chembl_id": drug_chembl,
        "primary_target_chembl_id": target_chembl,
        "target_count": len(rows),
        "pact_definition": "pAct = -log10(molar IC50/Ki/Kd); values are ChEMBL pchembl_value",
        "targets": rows,
    }
    if include_images:
        out["image_url"] = structure_image_url(drug_chembl)
    return out


def _class_hint(tid: str, target_type: str, primary_target: str) -> str:
    """Grounded class hint. Biological 'family' vs 'off-target' distinction is left to
    the persona (needs pathway/family knowledge); here we report what ChEMBL states."""
    if primary_target and tid == primary_target:
        return "primary target"
    if target_type == "CELL-LINE":
        return "cellular (antiproliferation)"
    if target_type == "SINGLE PROTEIN":
        return "secondary / off-target protein"
    return target_type.lower() if target_type else "unclassified"


async def _fetch_target_types(client, target_ids: list) -> dict:
    """Batched target_type lookup for a list of ChEMBL target ids."""
    types: dict = {}
    for i in range(0, len(target_ids), 40):
        chunk = target_ids[i:i + 40]
        r = await retryable_get(
            client, f"{BASE}/target.json",
            params={"target_chembl_id__in": ",".join(chunk), "format": "json", "limit": 50},
            timeout=20,
        )
        for t in r.json().get("targets", []):
            types[t.get("target_chembl_id")] = t.get("target_type", "")
    return types


# --------------------------------------------------------------------------- #
# Activity (compound / target potency rows)
# --------------------------------------------------------------------------- #
async def _fetch_activity(client, drug_chembl, target_chembl, params, include_images) -> dict:
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

    r = await retryable_get(client, f"{BASE}/activity.json", params=req_params, timeout=10)
    data = r.json()
    activities = data.get("activities", [])

    cleaned = []
    for a in activities:
        if not a.get("standard_value"):
            continue
        row = {
            "molecule_chembl_id": a.get("molecule_chembl_id"),
            "target_chembl_id": a.get("target_chembl_id"),
            "target_pref_name": a.get("target_pref_name"),
            "standard_type": a.get("standard_type"),
            "standard_value": a.get("standard_value"),
            "standard_units": a.get("standard_units"),
            "pchembl_value": a.get("pchembl_value"),
            "assay_description": (a.get("assay_description") or "")[:120],
        }
        if include_images and a.get("molecule_chembl_id"):
            row["image_url"] = structure_image_url(a.get("molecule_chembl_id"))
        cleaned.append(row)

    out = {"activities": cleaned, "count": data.get("page_meta", {}).get("total_count", len(cleaned))}
    if drug_chembl:
        out["molecule_chembl_id"] = drug_chembl
        if include_images:
            out["image_url"] = structure_image_url(drug_chembl)
    return out


async def _fetch_dataset(client, target_chembl, params, include_images) -> dict:
    if not target_chembl:
        return {}
    limit = min(params.get("limit", 10), 10)
    r = await retryable_get(
        client, f"{BASE}/activity.json",
        params={"target_chembl_id": target_chembl, "format": "json", "limit": limit},
        timeout=10,
    )
    data = r.json()
    total = data.get("page_meta", {}).get("total_count", 0)
    sample = []
    for a in data.get("activities", [])[:5]:
        row = {
            "molecule_chembl_id": a.get("molecule_chembl_id"),
            "standard_type": a.get("standard_type"),
            "standard_value": a.get("standard_value"),
            "standard_units": a.get("standard_units"),
        }
        if include_images and a.get("molecule_chembl_id"):
            row["image_url"] = structure_image_url(a.get("molecule_chembl_id"))
        sample.append(row)
    return {"dataset_count": total, "sample": sample, "target_chembl_id": target_chembl}
