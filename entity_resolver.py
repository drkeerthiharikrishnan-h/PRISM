"""
entity_resolver.py — Steps 1 & 2 of the PRISM pipeline + guardrails.

guardrail_check:        1 Haiku call → is query biomedical? Reject early if not.
Step 1 (parse_query):   1 LLM call → extract entity + target from free text.
Step 2 (resolve_ids):   Pure HTTP → map names to database IDs.
detect_persona:         1 LLM call → infer professional role from query language.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Optional

import httpx
from anthropic import AsyncAnthropic

_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
_CACHE_DIR = Path(__file__).parent / "cache"
_CACHE_DIR.mkdir(exist_ok=True)

PERSONA_IDS = ["medicinal_chemist", "pathologist", "cell_biologist", "comp_biologist"]

# ── Step 1: Parse query ───────────────────────────────────────────────────────

def _query_cache_key(query: str) -> Path:
    h = hashlib.md5(query.lower().strip().encode()).hexdigest()[:12]
    return _CACHE_DIR / f"parse_{h}.json"


async def parse_query(query: str) -> dict:
    """
    Extract entity + target from a free-text biomedical query.
    Returns: {"entity": str, "target": str, "entity_type": str}
    Cached by MD5 of query.
    """
    cache_file = _query_cache_key(query)
    if cache_file.exists():
        return json.loads(cache_file.read_text())

    system = (
        "You are a biomedical named-entity extractor. "
        "Given a biomedical query, extract:\n"
        "- entity: the primary drug/compound name (lowercase)\n"
        "- target: the primary protein/gene target name (uppercase gene symbol)\n"
        "- entity_type: one of 'drug', 'gene', 'protein', 'pathway'\n\n"
        "Return ONLY valid JSON with these three keys. No explanation."
    )
    user = f"Query: {query}"

    msg = await _client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=128,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    raw = msg.content[0].text.strip()
    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    result = json.loads(raw)
    cache_file.write_text(json.dumps(result))
    return result


# ── Step 2: Resolve IDs ───────────────────────────────────────────────────────

async def _pubchem_cid(entity: str, client: httpx.AsyncClient) -> Optional[str]:
    try:
        r = await client.get(
            f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{entity}/cids/JSON",
            timeout=8,
        )
        data = r.json()
        cids = data.get("IdentifierList", {}).get("CID", [])
        return str(cids[0]) if cids else None
    except Exception:
        return None


async def _chembl_molecule_id(entity: str, client: httpx.AsyncClient) -> Optional[str]:
    try:
        r = await client.get(
            "https://www.ebi.ac.uk/chembl/api/data/molecule/search.json",
            params={"q": entity, "limit": 1},
            timeout=8,
        )
        mols = r.json().get("molecules", [])
        return mols[0]["molecule_chembl_id"] if mols else None
    except Exception:
        return None


async def _uniprot_accession(target: str, client: httpx.AsyncClient) -> Optional[str]:
    try:
        r = await client.get(
            "https://rest.uniprot.org/uniprotkb/search",
            params={
                "query": f"gene:{target} AND organism_id:9606 AND reviewed:true",
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


async def _chembl_target_id(target: str, client: httpx.AsyncClient) -> Optional[str]:
    try:
        r = await client.get(
            "https://www.ebi.ac.uk/chembl/api/data/target/search.json",
            params={"q": target, "limit": 1},
            timeout=8,
        )
        targets = r.json().get("targets", [])
        return targets[0]["target_chembl_id"] if targets else None
    except Exception:
        return None


async def resolve_ids(entity: str, target: str) -> dict:
    """
    Map entity/target names to database IDs via parallel HTTP lookups.
    Falls back gracefully — missing IDs become None.
    """
    async with httpx.AsyncClient(
        headers={"User-Agent": "PRISM-HackathonBot/1.0"},
        follow_redirects=True,
    ) as client:
        import asyncio
        drug_cid, drug_chembl, target_uniprot, target_chembl = await asyncio.gather(
            _pubchem_cid(entity, client),
            _chembl_molecule_id(entity, client),
            _uniprot_accession(target, client),
            _chembl_target_id(target, client),
        )

    return {
        "entity": entity,
        "target": target,
        "drug_pubchem": drug_cid,
        "drug_chembl": drug_chembl,
        "target_uniprot": target_uniprot,
        "target_chembl": target_chembl,
    }


# ── Persona auto-detection ────────────────────────────────────────────────────

async def detect_persona(query: str) -> tuple[str, float]:
    """
    Infer professional persona from query phrasing.
    Returns (persona_id, confidence 0-1).
    Uses claude-haiku for speed/cost efficiency.
    """
    system = (
        "You are classifying a biomedical query by the professional role of the person who wrote it.\n\n"
        "The four roles are:\n"
        "- medicinal_chemist: asks about potency, SAR, IC50, scaffolds, co-crystals, analogues\n"
        "- pathologist: asks about mutations, resistance, clinical significance, patient outcomes, variants\n"
        "- cell_biologist: asks about pathways, signaling, mechanism of action, downstream effects, phosphorylation\n"
        "- comp_biologist: asks about structures, sequences, docking, datasets, pLDDT, modeling, simulation\n\n"
        "Return ONLY valid JSON: {\"persona_id\": \"<one of the four>\", \"confidence\": <0.0-1.0>}\n"
        "No explanation."
    )

    msg = await _client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=64,
        system=system,
        messages=[{"role": "user", "content": f"Query: {query}"}],
    )
    raw = msg.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    result = json.loads(raw)
    persona_id = result.get("persona_id", "medicinal_chemist")
    confidence = float(result.get("confidence", 0.5))
    if persona_id not in PERSONA_IDS:
        persona_id = "medicinal_chemist"
    return persona_id, confidence


# ── Guardrail ─────────────────────────────────────────────────────────────────

class GuardrailResult:
    def __init__(self, is_biomedical: bool, reason: str, suggestion: str):
        self.is_biomedical = is_biomedical
        self.reason        = reason
        self.suggestion    = suggestion


async def guardrail_check(query: str) -> GuardrailResult:
    """
    Fast pre-flight check — is this query biomedical?
    Uses Claude Haiku (~$0.0002 per call, <1s).

    Accepts: drug/compound queries, gene/protein questions, disease mechanism,
             pathway/signaling, clinical variants, structural biology, any life-sciences topic.
    Rejects: general knowledge, greetings, math, weather, coding, politics, etc.

    Returns GuardrailResult with is_biomedical flag + helpful message if rejected.
    """
    system = """You are a guardrail for a biomedical research tool called PRISM.

PRISM can only answer questions about:
- Drugs, compounds, small molecules (e.g. imatinib, aspirin, gefitinib)
- Genes, proteins, enzymes, kinases (e.g. ABL1, EGFR, BRCA1, TP53)
- Diseases and their molecular basis (e.g. CML, lung cancer, Alzheimer's)
- Biological pathways and signaling (e.g. MAPK, PI3K/AKT, apoptosis)
- Drug-target interactions, binding affinity, SAR, resistance mutations
- Clinical variants, biomarkers, diagnostics
- Protein structures, sequences, docking, molecular modeling
- Anything in biomedical research, pharmacology, biochemistry, or molecular biology

PRISM cannot answer:
- General knowledge questions (weather, history, politics, sports, math)
- Greetings or casual conversation (hello, hi, how are you)
- Coding or software questions
- Business, finance, or legal questions
- Creative writing or personal advice

Classify the query. Return ONLY valid JSON:
{
  "is_biomedical": true or false,
  "reason": "one short sentence why",
  "suggestion": "if false — one example of a valid PRISM query the user could try instead; if true — empty string"
}
No explanation outside the JSON."""

    try:
        msg = await _client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=150,
            system=system,
            messages=[{"role": "user", "content": f"Query: {query}"}],
        )
        raw = msg.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        result     = json.loads(raw)
        is_bio     = bool(result.get("is_biomedical", True))
        reason     = result.get("reason", "")
        suggestion = result.get("suggestion", "")
        return GuardrailResult(is_bio, reason, suggestion)
    except Exception:
        # If guardrail itself fails, let the query through (fail open)
        return GuardrailResult(True, "", "")
