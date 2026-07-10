"""
orchestrator.py — Steps 3, 4, 5 of the PRISM pipeline.

Step 3 (get_persona_plan):  Load YAML config → connector call list.
Step 4 (retrieve_all):      Call all connectors in parallel.
Step 5 (synthesize_stream): One streaming Claude call per persona.

stream_pipeline():  Full async generator — yields SSE events consumed by main.py.
run_pipeline():     Non-streaming version for cache pre-fetch.
"""
import asyncio
import json
import logging
import os
import re
from pathlib import Path
from typing import AsyncIterator, Optional

logger = logging.getLogger(__name__)

import yaml
from anthropic import AsyncAnthropic

from connectors import REGISTRY
from entity_resolver import parse_query, resolve_ids, guardrail_check

_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
PERSONAS_DIR = Path(__file__).parent / "personas"
CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

_FORMATTER_PATH = Path(__file__).parent / "prompts" / "response_formatter.txt"
_RESPONSE_FORMATTER = _FORMATTER_PATH.read_text(encoding="utf-8") if _FORMATTER_PATH.exists() else "{persona_prompt}"

PERSONA_ORDER = ["medicinal_chemist", "pathologist", "cell_molecular_biologist", "computational_biologist"]


# ── Load persona configs ──────────────────────────────────────────────────────

def _load_persona(persona_id: str) -> dict:
    path = PERSONAS_DIR / f"{persona_id}.yaml"
    return yaml.safe_load(path.read_text())


def _load_all_personas() -> dict[str, dict]:
    return {p: _load_persona(p) for p in PERSONA_ORDER}


# ── Step 3: Persona plan ──────────────────────────────────────────────────────

def get_persona_plan(persona_cfg: dict, entity_ids: dict) -> list[dict]:
    """Return list of {name, entity_ids, params} calls.

    Supports both old dict format [{name, params}] and new string list format.
    Params for string-format connectors are sourced from connector_bindings if present.
    """
    raw = persona_cfg.get("connectors", [])
    bindings = persona_cfg.get("connector_bindings", {})
    plan = []
    for c in raw:
        if isinstance(c, str):
            plan.append({"name": c, "entity_ids": entity_ids, "params": {}})
        else:
            plan.append({"name": c["name"], "entity_ids": entity_ids, "params": c.get("params", {})})
    return plan


# ── Step 4: Retrieve ──────────────────────────────────────────────────────────

async def retrieve_for_persona(persona_id: str, persona_cfg: dict, entity_ids: dict) -> dict:
    """Call all connectors for one persona in parallel."""
    plan = get_persona_plan(persona_cfg, entity_ids)
    tasks = [REGISTRY[step["name"]](step["entity_ids"], step["params"]) for step in plan]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    evidence: dict = {}
    for step, result in zip(plan, results):
        if isinstance(result, Exception):
            evidence[step["name"]] = {"error": str(result)}
        else:
            evidence[step["name"]] = result
    return evidence


# ── Step 5: Synthesize (streaming) ───────────────────────────────────────────

_PERSONA_QUESTION_TEMPLATES = {
    "medicinal_chemist": "What are the IC50/Ki/Kd binding affinities, co-crystal PDB structures, and SAR trends for {entity} at {target}?",
    "pathologist":       "Which {target} resistance mutations emerge under {entity} treatment, and what is their clinical significance?",
    "cell_molecular_biologist":  "How does {entity} disrupt {target} signaling pathways, and what are the downstream cellular consequences?",
    "computational_biologist":   "What experimental PDB structures, AlphaFold predictions, and ML-ready bioactivity datasets exist for {entity}–{target}?",
}

def _build_persona_question(persona_id: str, entity_ids: dict, original_query: str) -> str:
    """Rephrase the original query through the persona's professional lens."""
    entity = entity_ids.get("entity", "")
    target = entity_ids.get("target", "")
    template = _PERSONA_QUESTION_TEMPLATES.get(persona_id)
    if template and entity and target:
        return template.format(entity=entity, target=target)
    return original_query

def _build_synthesis_prompt(persona_cfg: dict, entity_ids: dict, evidence: dict) -> tuple[str, str, int]:
    """Build system + user messages for synthesis LLM call. Returns (system, user, max_citation_idx)."""
    persona_prompt = (persona_cfg.get("system_prompt") or persona_cfg.get("synthesis_prompt", "")).strip()
    system = _RESPONSE_FORMATTER.replace("{persona_prompt}", persona_prompt)

    # Number evidence pieces as [E1], [E2], ...
    evidence_lines = []
    idx = 1
    for connector_name, data in evidence.items():
        if not data or "error" in data:
            continue
        evidence_lines.append(f"[E{idx}] {connector_name.upper()}: {json.dumps(data, indent=2)[:800]}")
        idx += 1

    # PubMed abstracts as numbered evidence
    pubmed = evidence.get("pubmed", {})
    for abstract in pubmed.get("abstracts", []):
        title = abstract.get("title", "")
        text = abstract.get("abstract", "")
        evidence_lines.append(f"[E{idx}] PUBMED PMID:{abstract.get('pmid', '')}: {title}. {text[:400]}")
        idx += 1

    max_idx = idx - 1
    if max_idx > 0:
        system += (
            f"\n\nCITATION RULES: You have exactly {max_idx} evidence item(s), "
            f"[E1] through [E{max_idx}]. Never cite beyond [E{max_idx}]. "
            "Write each citation as a standalone marker like [E1], never combined like [E1,E2]."
        )

    user_payload = {
        "question": f"What do I need to know about {entity_ids['entity']} and its target {entity_ids['target']}?",
        "structured_evidence": "\n\n".join(evidence_lines) if evidence_lines else "No evidence retrieved.",
    }
    return system, json.dumps(user_payload), max_idx


async def _validated_citation_stream(
    token_stream: AsyncIterator[str],
    max_idx: int,
) -> AsyncIterator[str]:
    """Pass-through stream that strips invalid [E#] citation markers.

    Buffers only while inside a [...] block; normal text is yielded immediately
    so streaming UX is preserved.
    """
    buf = ""
    async for chunk in token_stream:
        buf += chunk
        while True:
            open_pos = buf.find("[")
            if open_pos == -1:
                yield buf
                buf = ""
                break
            if open_pos > 0:
                yield buf[:open_pos]
                buf = buf[open_pos:]
            # buf now starts with "["
            close_pos = buf.find("]")
            if close_pos == -1:
                break  # incomplete marker — wait for more tokens
            candidate = buf[: close_pos + 1]
            buf = buf[close_pos + 1 :]
            m = re.fullmatch(r"\[E(\d+)\]", candidate)
            if m:
                n = int(m.group(1))
                if 1 <= n <= max_idx:
                    yield candidate  # valid citation
                else:
                    logger.warning("PRISM: stripped hallucinated citation %r (valid E1–E%d)", candidate, max_idx)
            else:
                yield candidate  # not a citation marker — pass through unchanged
    if buf:
        yield buf


def _connector_detail(name: str, data: dict) -> str:
    """One-line human-readable summary of what a connector returned."""
    try:
        if name == "pubmed":
            n = len(data.get("abstracts", []))
            return f"{n} abstract{'s' if n != 1 else ''}"
        if name == "chembl":
            n = len(data.get("activities", []))
            count = data.get("count", n)
            pref = data.get("pref_name", "")
            label = f"{pref} — " if pref else ""
            return f"{label}{count} bioactivit{'ies' if count != 1 else 'y'}"
        if name == "admet":
            pref = data.get("pref_name", "")
            mw = data.get("molecular_weight")
            alogp = data.get("alogp")
            parts = []
            if pref:
                parts.append(pref)
            if mw:
                parts.append(f"MW {mw}")
            if alogp is not None:
                parts.append(f"logP {alogp}")
            return " · ".join(parts) if parts else "properties retrieved"
        if name == "uniprot":
            acc = data.get("accession", "")
            gene = data.get("gene_name", "")
            return f"{acc}{' · ' + gene if gene else ''}"
        if name == "clinvar":
            n = len(data.get("variants", []))
            gene = data.get("gene", "")
            return f"{n} variant{'s' if n != 1 else ''}{' for ' + gene if gene else ''}"
        if name == "pdb":
            n = len(data.get("structures", []))
            return f"{n} structure{'s' if n != 1 else ''}"
        if name == "alphafold":
            acc = data.get("accession", "")
            plddt = data.get("plddt_global")
            avail = data.get("available", True)
            if not avail:
                return f"{acc} — no model available"
            return f"{acc}{f' · pLDDT {plddt:.0f}' if plddt else ''}"
        if name == "interpro":
            n = data.get("entry_count", len(data.get("entries", [])))
            return f"{n} domain entr{'ies' if n != 1 else 'y'}"
        if name == "string":
            n = len(data.get("partners", []))
            return f"{n} PPI partner{'s' if n != 1 else ''}"
        if name == "reactome":
            n = len(data.get("pathways", []))
            return f"{n} pathway{'s' if n != 1 else ''}"
        if name == "gtex":
            n = len(data.get("top_tissues", []))
            unit = data.get("unit", "TPM")
            return f"top {n} tissues by expression ({unit})"
        if name == "opentargets":
            n = len(data.get("associated_diseases", []))
            drugs = data.get("drug_candidate_count", 0)
            return f"{n} disease association{'s' if n != 1 else ''}{f' · {drugs} drug candidates' if drugs else ''}"
        if name == "proteinatlas":
            pathology = data.get("pathology_total", 0)
            micro = data.get("microscopy_total", 0)
            return f"{pathology} pathology · {micro} microscopy image{'s' if micro != 1 else ''}"
        if name == "pubchem":
            cid = data.get("CID") or data.get("cid", "")
            return f"CID {cid}" if cid else "compound data"
        keys = [k for k in data if k != "error"]
        return f"{len(keys)} field{'s' if len(keys) != 1 else ''}"
    except Exception:
        return "data retrieved"


def _summarize_evidence(evidence: dict) -> list[dict]:
    """Connector-level summary list for the observability panel."""
    summaries = []
    for name, data in evidence.items():
        if not data:
            summaries.append({"name": name, "status": "empty", "detail": "no data returned"})
        elif "error" in data:
            summaries.append({"name": name, "status": "error", "detail": str(data["error"])[:80]})
        else:
            summaries.append({"name": name, "status": "ok", "detail": _connector_detail(name, data)})
    return summaries


async def synthesize_stream(
    persona_id: str,
    persona_cfg: dict,
    entity_ids: dict,
    evidence: dict,
) -> AsyncIterator[str]:
    """Yield markdown text tokens for one persona via Claude streaming."""
    system, user, max_idx = _build_synthesis_prompt(persona_cfg, entity_ids, evidence)

    async with _client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1200,
        system=system,
        messages=[{"role": "user", "content": user}],
    ) as stream:
        async for token in _validated_citation_stream(stream.text_stream, max_idx):
            yield token


# ── Cache helpers ─────────────────────────────────────────────────────────────

def _cache_key(entity: str, target: str) -> Path:
    name = f"{entity}_{target}".lower().replace(" ", "_")
    return CACHE_DIR / f"{name}.json"


def _load_cache(entity: str, target: str) -> Optional[dict]:
    path = _cache_key(entity, target)
    if path.exists():
        return json.loads(path.read_text())
    return None


def _save_cache(entity: str, target: str, data: dict) -> None:
    _cache_key(entity, target).write_text(json.dumps(data, indent=2))


# ── Main pipeline: streaming ──────────────────────────────────────────────────

async def stream_pipeline(
    query: str,
    persona: Optional[str],
    demo_mode: bool,
) -> AsyncIterator[dict]:
    """
    Full async generator yielding SSE event dicts:
      {"type": "status",  "stage": str, "message": str}
      {"type": "token",   "persona": str, "text": str}
      {"type": "done",    "metadata": dict}
    """
    personas_to_run = [persona] if persona and persona in PERSONA_ORDER else PERSONA_ORDER

    # ── Stage: guardrail ──
    if not demo_mode:
        yield {"type": "status", "stage": "checking", "message": "Checking query…"}
        guard = await guardrail_check(query)
        if not guard.is_biomedical:
            yield {
                "type": "guardrail_rejected",
                "reason": guard.reason,
                "suggestion": guard.suggestion,
            }
            return   # stop pipeline — no LLM synthesis calls made

    # ── Stage: parse ──
    yield {"type": "status", "stage": "parsing", "message": "Extracting entity and target…"}
    parsed = await parse_query(query)
    entity = parsed.get("entity", "")
    target = parsed.get("target", "")
    yield {"type": "status", "stage": "parsed", "message": f"Identified: {entity} → {target}"}

    # ── Stage: resolve or demo cache ──
    if demo_mode:
        cached = _load_cache(entity, target)
        if cached:
            yield {"type": "status", "stage": "cache", "message": "Loading demo cache…"}
            all_evidence = cached.get("evidence", {})
            entity_ids = cached.get("ids", {"entity": entity, "target": target})
        else:
            demo_mode = False  # cache miss → fall through to live

    if not demo_mode:
        yield {"type": "status", "stage": "resolving", "message": "Resolving database IDs…"}
        entity_ids = await resolve_ids(entity, target)
        yield {
            "type": "status",
            "stage": "resolved",
            "message": (
                f"ChEMBL: {entity_ids.get('drug_chembl') or '?'} · "
                f"UniProt: {entity_ids.get('target_uniprot') or '?'}"
            ),
        }

        # ── Stage: retrieve ──
        yield {"type": "status", "stage": "retrieving", "message": "Querying biomedical databases…"}
        all_personas_cfg = _load_all_personas()
        retrieve_tasks = {
            p: retrieve_for_persona(p, all_personas_cfg[p], entity_ids)
            for p in personas_to_run
        }
        gathered = await asyncio.gather(*retrieve_tasks.values(), return_exceptions=True)
        all_evidence = {}
        for p, result in zip(retrieve_tasks.keys(), gathered):
            all_evidence[p] = result if not isinstance(result, Exception) else {}

        yield {"type": "status", "stage": "retrieved", "message": "Data gathered — synthesizing responses…"}

        # Save cache for future demo use
        if set(personas_to_run) == set(PERSONA_ORDER):
            _save_cache(entity, target, {"ids": entity_ids, "evidence": all_evidence})

    else:
        all_personas_cfg = _load_all_personas()
        yield {"type": "status", "stage": "retrieved", "message": "Demo data loaded — synthesizing responses…"}

    # ── Stage: synthesize all personas concurrently ──
    async def stream_one_persona(persona_id: str) -> None:
        """Inner coroutine — streams tokens for one persona."""
        cfg = all_personas_cfg[persona_id]
        evidence = all_evidence.get(persona_id, {}) if not demo_mode else all_evidence.get(persona_id, {})
        await token_queue.put({
            "type": "persona_question",
            "persona": persona_id,
            "question": _build_persona_question(persona_id, entity_ids, query),
            "original_query": query,
        })
        await token_queue.put({
            "type": "evidence",
            "persona": persona_id,
            "connectors": _summarize_evidence(evidence),
        })
        async for token in synthesize_stream(persona_id, cfg, entity_ids, evidence):
            await token_queue.put({"type": "token", "persona": persona_id, "text": token})
        await token_queue.put({"type": "_done_persona", "persona": persona_id})

    token_queue: asyncio.Queue = asyncio.Queue()
    tasks = [asyncio.create_task(stream_one_persona(p)) for p in personas_to_run]
    finished = 0

    while finished < len(personas_to_run):
        event = await token_queue.get()
        if event["type"] == "_done_persona":
            finished += 1
        else:
            yield event

    await asyncio.gather(*tasks)

    # ── Done ──
    dbs_queried = set()
    for p in personas_to_run:
        cfg = _load_persona(p)
        for c in cfg.get("connectors", []):
            dbs_queried.add(c if isinstance(c, str) else c["name"])

    yield {
        "type": "done",
        "metadata": {
            "entity": entity,
            "target": target,
            "entity_ids": entity_ids if not demo_mode else {},
            "personas_run": personas_to_run,
            "databases_queried": sorted(dbs_queried),
            "llm_calls": 1 + len(personas_to_run),
        },
    }


# ── Non-streaming pipeline (for cache pre-fetch) ──────────────────────────────

async def run_pipeline(query: str, personas: list[str] = PERSONA_ORDER) -> dict:
    """Run the full pipeline without streaming — used for pre-fetching demo cache."""
    parsed = await parse_query(query)
    entity = parsed.get("entity", "")
    target = parsed.get("target", "")
    entity_ids = await resolve_ids(entity, target)

    all_personas_cfg = _load_all_personas()
    retrieve_tasks = {
        p: retrieve_for_persona(p, all_personas_cfg[p], entity_ids)
        for p in personas
    }
    gathered = await asyncio.gather(*retrieve_tasks.values(), return_exceptions=True)
    all_evidence = {p: r for p, r in zip(retrieve_tasks.keys(), gathered) if not isinstance(r, Exception)}

    results: dict[str, str] = {}
    for persona_id in personas:
        cfg = all_personas_cfg[persona_id]
        evidence = all_evidence.get(persona_id, {})
        tokens = []
        async for token in synthesize_stream(persona_id, cfg, entity_ids, evidence):
            tokens.append(token)
        results[persona_id] = "".join(tokens)

    output = {"entity": entity, "target": target, "ids": entity_ids, "responses": results, "evidence": all_evidence}
    _save_cache(entity, target, {"ids": entity_ids, "evidence": all_evidence})
    return output
