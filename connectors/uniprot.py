"""UniProt connector — protein function, sequence, GO terms. Cell biologist + comp biologist."""
import httpx
from connectors.utils import retryable_get

BASE = "https://rest.uniprot.org/uniprotkb"


async def fetch(entity_ids: dict, params: dict) -> dict:
    """
    params:
      fields: list[str]  e.g. ["cc_function", "go", "sequence", "ft_binding", "ft_domain"]
    Returns:
      {"accession": str, "gene": str, "function": str, "go_terms": [...],
       "sequence_length": int, "binding_sites": [...], "domains": [...]}
    """
    accession = entity_ids.get("target_uniprot")
    target = entity_ids.get("target", "")

    if not accession:
        # Try to look it up
        accession = await _lookup_accession(target)
    if not accession:
        return {}

    fields = params.get("fields", ["cc_function", "go"])
    field_str = ",".join(fields + ["gene_names", "protein_name"])

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            r = await retryable_get(
                client, f"{BASE}/{accession}.json",
                params={"fields": field_str},
                timeout=10,
            )
            d = r.json()
            return _parse_uniprot(d, accession)
    except Exception as e:
        return {"accession": accession, "error": str(e)}


async def _lookup_accession(gene: str) -> str | None:
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            r = await retryable_get(
                client, f"{BASE}/search",
                params={
                    "query": f"gene:{gene} AND organism_id:9606 AND reviewed:true",
                    "fields": "accession",
                    "format": "json",
                    "size": 1,
                },
                timeout=8,
            )
            results = r.json().get("results", [])
            return results[0]["primaryAccession"] if results else None
    except Exception:
        return None


def _parse_uniprot(d: dict, accession: str) -> dict:
    result: dict = {"accession": accession}

    # Gene names
    genes = d.get("genes", [])
    if genes:
        result["gene"] = genes[0].get("geneName", {}).get("value", "")

    # Function comment
    for comment in d.get("comments", []):
        if comment.get("commentType") == "FUNCTION":
            texts = comment.get("texts", [])
            if texts:
                result["function"] = texts[0].get("value", "")[:600]

    # GO terms
    go_terms = []
    for ref in d.get("uniProtKBCrossReferences", []):
        if ref.get("database") == "GO":
            props = {p["key"]: p["value"] for p in ref.get("properties", [])}
            go_terms.append({"id": ref.get("id"), "term": props.get("GoTerm", "")[:80]})
    result["go_terms"] = go_terms[:8]

    # Sequence length
    seq = d.get("sequence", {})
    result["sequence_length"] = seq.get("length")

    # Binding sites & domains from features
    binding_sites = []
    domains = []
    for feat in d.get("features", []):
        ft = feat.get("type", "")
        loc = feat.get("location", {})
        desc = feat.get("description", "")
        start = loc.get("start", {}).get("value")
        end = loc.get("end", {}).get("value")
        if ft in ("Binding site", "Active site"):
            binding_sites.append({"type": ft, "position": f"{start}-{end}", "description": desc})
        elif ft == "Domain":
            domains.append({"name": desc, "range": f"{start}-{end}"})

    result["binding_sites"] = binding_sites[:6]
    result["domains"] = domains[:4]

    return result
