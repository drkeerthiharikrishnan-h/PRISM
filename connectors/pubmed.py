"""PubMed connector — NCBI E-utilities. Used by all 4 personas."""
import os
from typing import Any
import httpx
from connectors.utils import retryable_get

NCBI_KEY = os.getenv("NCBI_API_KEY", "")
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


async def fetch(entity_ids: dict, params: dict) -> dict:
    """
    Search PubMed and return top abstracts.
    params:
      keywords: list[str]  — extra terms to AND with entity+target
    Returns:
      {"abstracts": [{"pmid": str, "title": str, "abstract": str}]}
    """
    entity = entity_ids.get("entity", "")
    target = entity_ids.get("target", "")
    keywords = params.get("keywords", [])

    term_parts = []
    if entity:
        term_parts.append(entity)
    if target:
        term_parts.append(target)
    if keywords:
        kw_str = " OR ".join(f'"{k}"' for k in keywords[:4])
        term_parts.append(f"({kw_str})")
    term = " AND ".join(term_parts) if term_parts else entity or target or "biomedical"

    base_params: dict[str, Any] = {
        "db": "pubmed",
        "term": term,
        "retmax": 5,
        "retmode": "json",
        "sort": "relevance",
    }
    if NCBI_KEY:
        base_params["api_key"] = NCBI_KEY

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            # Search
            r = await retryable_get(client, f"{BASE}/esearch.fcgi", params=base_params, timeout=10)
            ids = r.json().get("esearchresult", {}).get("idlist", [])
            if not ids:
                return {"abstracts": []}

            # Fetch summaries
            r2 = await retryable_get(
                client, f"{BASE}/efetch.fcgi",
                params={
                    "db": "pubmed",
                    "id": ",".join(ids),
                    "retmode": "xml",
                    "rettype": "abstract",
                    **({"api_key": NCBI_KEY} if NCBI_KEY else {}),
                },
                timeout=10,
            )
            # Parse titles + abstracts from XML (simple approach without full XML parser)
            xml = r2.text
            abstracts = _parse_pubmed_xml(xml, ids)
            return {"abstracts": abstracts}

    except Exception as e:
        return {"abstracts": [], "error": str(e)}


def _parse_pubmed_xml(xml: str, ids: list[str]) -> list[dict]:
    """Minimal XML parser — extracts ArticleTitle + AbstractText blocks."""
    import re
    articles = re.split(r"<PubmedArticle>", xml)[1:]
    results = []
    for i, article in enumerate(articles):
        title_m = re.search(r"<ArticleTitle>(.*?)</ArticleTitle>", article, re.DOTALL)
        abstract_m = re.search(r"<AbstractText[^>]*>(.*?)</AbstractText>", article, re.DOTALL)
        title = re.sub(r"<[^>]+>", "", title_m.group(1)).strip() if title_m else ""
        abstract = re.sub(r"<[^>]+>", "", abstract_m.group(1)).strip() if abstract_m else ""
        pmid = ids[i] if i < len(ids) else ""
        if title or abstract:
            results.append({"pmid": pmid, "title": title, "abstract": abstract[:600]})
    return results
