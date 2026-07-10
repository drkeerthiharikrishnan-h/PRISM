"""Open Targets connector — target-disease associations + drug candidates."""
from typing import Optional

import httpx

from connectors.utils import retryable_post

GQL = "https://api.platform.opentargets.org/api/v4/graphql"


async def fetch(entity_ids: dict, params: dict) -> dict:
    """Return disease associations and clinical candidates for the target."""
    ensembl = entity_ids.get("target_ensembl")
    symbol = entity_ids.get("target", "")
    size = int(params.get("size", 5))

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            if not ensembl and symbol:
                ensembl = await _resolve_ensembl(client, symbol)
            if not ensembl:
                return {"associated_diseases": [], "drug_candidates": []}

            query = {
                "query": """query($e:String!,$n:Int!){
                  target(ensemblId:$e){
                    approvedSymbol
                    associatedDiseases(page:{index:0,size:$n}){ rows{ disease{ id name } score } }
                    drugAndClinicalCandidates{ count rows{ maxClinicalStage drug{ name } } }
                  }
                }""",
                "variables": {"e": ensembl, "n": size},
            }
            response = await retryable_post(client, GQL, json=query, timeout=12)
            target = ((response.json().get("data") or {}).get("target")) or {}
            diseases = [
                {
                    "disease_id": row["disease"]["id"],
                    "name": row["disease"]["name"],
                    "score": round(row.get("score", 0.0), 4),
                }
                for row in ((target.get("associatedDiseases") or {}).get("rows") or [])
            ]
            drug_candidates_raw = target.get("drugAndClinicalCandidates") or {}
            drugs = [
                {
                    "drug": (row.get("drug") or {}).get("name", ""),
                    "max_clinical_stage": row.get("maxClinicalStage", ""),
                }
                for row in (drug_candidates_raw.get("rows") or [])
            ]
            return {
                "target": target.get("approvedSymbol") or symbol,
                "ensembl_id": ensembl,
                "associated_diseases": diseases,
                "drug_candidate_count": drug_candidates_raw.get("count", len(drugs)),
                "drug_candidates": drugs,
            }
    except Exception as exc:
        return {"associated_diseases": [], "drug_candidates": [], "error": str(exc)}


async def _resolve_ensembl(client: httpx.AsyncClient, symbol: str) -> Optional[str]:
    query = {
        "query": "query($q:String!){search(queryString:$q,entityNames:[\"target\"],page:{index:0,size:1}){hits{id}}}",
        "variables": {"q": symbol},
    }
    response = await retryable_post(client, GQL, json=query, timeout=10)
    hits = ((response.json().get("data", {}) or {}).get("search", {}) or {}).get("hits", [])
    return hits[0]["id"] if hits else None
