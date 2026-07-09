"""Open Targets connector — target-disease associations and drug candidates."""
import httpx
from connectors.utils import retryable_post

BASE = "https://api.platform.opentargets.org/api/v4/graphql"


async def fetch(entity_ids: dict, params: dict) -> dict:
    target = entity_ids.get("target", "")
    ensembl_id = entity_ids.get("target_ensembl", "")
    size = min(params.get("size", 5), 10)

    if not ensembl_id and not target:
        return {}

    # Resolve Ensembl ID via search if not already known
    if not ensembl_id:
        ensembl_id = await _resolve_ensembl(target)
    if not ensembl_id:
        return {"error": f"Could not resolve Ensembl ID for {target}"}

    query = """
    query TargetInfo($ensemblId: String!, $size: Int!) {
      target(ensemblId: $ensemblId) {
        id
        approvedSymbol
        associatedDiseases(page: { index: 0, size: $size }) {
          rows {
            disease { id name }
            score
          }
        }
        knownDrugs(size: $size) {
          rows {
            drug { name maximumClinicalTrialPhase }
          }
        }
      }
    }
    """
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            r = await retryable_post(
                client, BASE,
                json={"query": query, "variables": {"ensemblId": ensembl_id, "size": size}},
                timeout=15,
            )
            data = r.json().get("data", {}).get("target") or {}
            if not data:
                return {"ensembl_id": ensembl_id, "error": "Target not found in Open Targets"}

            diseases = [
                {"disease_id": row["disease"]["id"], "name": row["disease"]["name"], "score": round(row["score"], 3)}
                for row in (data.get("associatedDiseases") or {}).get("rows", [])
            ]
            drugs_raw = (data.get("knownDrugs") or {}).get("rows", [])
            drugs = [
                {"drug": r["drug"]["name"], "max_clinical_stage": r["drug"]["maximumClinicalTrialPhase"]}
                for r in drugs_raw
            ]
            return {
                "ensembl_id": ensembl_id,
                "associated_diseases": diseases,
                "drug_candidate_count": len(drugs),
                "drug_candidates": drugs[:5],
            }
    except Exception as e:
        return {"error": str(e)}


async def _resolve_ensembl(gene_symbol: str) -> str:
    query = """
    query Search($q: String!) {
      search(queryString: $q, entityNames: ["target"], page: { index: 0, size: 1 }) {
        hits { id }
      }
    }
    """
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            r = await retryable_post(
                client, BASE,
                json={"query": query, "variables": {"q": gene_symbol}},
                timeout=10,
            )
            hits = r.json().get("data", {}).get("search", {}).get("hits", [])
            return hits[0]["id"] if hits else ""
    except Exception:
        return ""
