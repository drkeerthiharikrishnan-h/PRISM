"""GTEx connector — tissue expression data. GTEx Portal v2 API."""
import httpx
from connectors.utils import retryable_get

BASE = "https://gtexportal.org/api/v2"


async def fetch(entity_ids: dict, params: dict) -> dict:
    target = entity_ids.get("target", "")
    gencode_id = entity_ids.get("target_gencode", "")
    dataset_id = params.get("dataset_id", "gtex_v8")
    top_n = min(params.get("top_n", 5), 10)

    if not target and not gencode_id:
        return {}

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            # Resolve gencode ID if not provided
            if not gencode_id:
                gencode_id = await _resolve_gencode(client, target, dataset_id)
            if not gencode_id:
                return {"error": f"Could not resolve Gencode ID for {target}"}

            r = await retryable_get(
                client, f"{BASE}/expression/geneExpression",
                params={"datasetId": dataset_id, "gencodeId": gencode_id, "format": "json"},
                timeout=12,
            )
            if r.status_code != 200:
                return {}

            data = r.json()
            medians = data.get("data", [])
            sorted_tissues = sorted(medians, key=lambda x: x.get("median", 0), reverse=True)
            unit = data.get("unit", "TPM")

            return {
                "gencode_id": gencode_id,
                "unit": unit,
                "top_tissues": [
                    {"tissue": t.get("tissueSiteDetailId", ""), "median": t.get("median", 0)}
                    for t in sorted_tissues[:top_n]
                ],
                "expression": [
                    {"tissue": t.get("tissueSiteDetailId", ""), "median": t.get("median", 0)}
                    for t in sorted_tissues[:20]
                ],
            }
    except Exception as e:
        return {"error": str(e)}


async def _resolve_gencode(client: httpx.AsyncClient, gene_symbol: str, dataset_id: str) -> str:
    try:
        r = await retryable_get(
            client, f"{BASE}/reference/gene",
            params={"geneSymbol": gene_symbol, "datasetId": dataset_id, "format": "json"},
            timeout=8,
        )
        if r.status_code != 200:
            return ""
        genes = r.json().get("data", [])
        return genes[0].get("gencodeId", "") if genes else ""
    except Exception:
        return ""
