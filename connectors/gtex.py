"""GTEx connector — bulk-tissue median gene expression."""
from typing import Optional

import httpx

from connectors.utils import retryable_get

BASE = "https://gtexportal.org/api/v2"


async def fetch(entity_ids: dict, params: dict) -> dict:
    """Return GTEx tissue expression for the target gene."""
    gencode = entity_ids.get("target_gencode")
    symbol = entity_ids.get("target", "")
    dataset = params.get("dataset_id", "gtex_v8")
    top_n = int(params.get("top_n", 5))

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            if not gencode and symbol:
                gencode = await _resolve_gencode(client, symbol)
            if not gencode:
                return {"expression": [], "top_tissues": []}

            response = await retryable_get(
                client,
                f"{BASE}/expression/medianGeneExpression",
                params={"datasetId": dataset, "gencodeId": gencode},
                timeout=15,
            )
            rows = response.json().get("data", [])
            expression = [
                {"tissue": row.get("tissueSiteDetailId"), "median": row.get("median")}
                for row in rows
            ]
            unit = rows[0].get("unit", "TPM") if rows else "TPM"
            top_tissues = sorted(expression, key=lambda row: row.get("median") or 0, reverse=True)[:top_n]
            return {
                "gene": (rows[0].get("geneSymbol") if rows else symbol) or symbol,
                "gencode_id": gencode,
                "unit": unit,
                "top_tissues": top_tissues,
                "expression": expression,
            }
    except Exception as exc:
        return {"expression": [], "top_tissues": [], "error": str(exc)}


async def _resolve_gencode(client: httpx.AsyncClient, symbol: str) -> Optional[str]:
    response = await retryable_get(client, f"{BASE}/reference/gene", params={"geneId": symbol}, timeout=10)
    data = response.json().get("data", [])
    return data[0].get("gencodeId") if data else None
