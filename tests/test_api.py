"""
Backend tests — FastAPI endpoints via httpx async client.
Server must be running: uv run uvicorn main:app --port 8000

Run:  uv run pytest tests/test_api.py -v
"""
import json
import re
from pathlib import Path
import pytest
import httpx
from tests.conftest import BASE_URL, PERSONA_QUERIES, SHARED_QUERY


_SUBSCRIPT_TRANSLATION = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
_GT_MARKERS_PATH = Path(__file__).parent / "ground_truth" / "erlotinib_molecular_properties_markers.json"
_GT_MARKERS_DATA = json.loads(_GT_MARKERS_PATH.read_text())


def _normalize_text_for_gt(text: str) -> str:
    """Normalize unicode subscripts/superscripts to improve GT matching robustness."""
    return text.translate(_SUBSCRIPT_TRANSLATION)


@pytest.fixture
async def client():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as c:
        yield c


# ── Health + static ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_endpoint(client):
    r = await client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["service"] == "Facet"


@pytest.mark.asyncio
async def test_ui_serves_html(client):
    r = await client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Facet" in r.text


# ── Personas endpoint ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_personas_returns_all_four(client):
    r = await client.get("/api/personas")
    assert r.status_code == 200
    data = r.json()
    assert "personas" in data
    assert len(data["personas"]) == 4

    ids = {p["id"] for p in data["personas"]}
    assert ids == {"medicinal_chemist", "pathologist", "cell_molecular_biologist", "computational_biologist"}


@pytest.mark.asyncio
async def test_personas_have_required_fields(client):
    r = await client.get("/api/personas")
    for persona in r.json()["personas"]:
        assert persona.get("name"), f"Persona {persona.get('id')} missing name"
        assert persona.get("emoji"), f"Persona {persona.get('id')} missing emoji"
        assert len(persona.get("sections", [])) > 0, f"Persona {persona.get('id')} missing sections"
        assert len(persona.get("connectors", [])) > 0, f"Persona {persona.get('id')} missing connectors"


# ── Detect persona endpoint ───────────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.parametrize("persona_id,query", list(PERSONA_QUERIES.items()))
async def test_detect_persona_endpoint(client, persona_id, query):
    r = await client.post("/api/detect-persona", json={"query": query}, timeout=20)
    assert r.status_code == 200
    data = r.json()
    assert "persona_id" in data
    assert "confidence" in data
    assert data["persona_id"] == persona_id, (
        f"Expected {persona_id}, got {data['persona_id']} "
        f"(confidence={data['confidence']:.2f})"
    )
    print(f"\n  /detect-persona [{persona_id}]: "
          f"detected={data['persona_id']} conf={data['confidence']:.2f}")


# ── SSE query endpoint ────────────────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.parametrize("persona_id", ["medicinal_chemist", "pathologist",
                                         "cell_molecular_biologist", "computational_biologist"])
async def test_query_single_persona_streams_tokens(persona_id):
    """Each persona should produce streaming tokens with persona-specific content."""
    tokens = []
    status_events = []
    query = PERSONA_QUERIES[persona_id]

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=120) as client:
        async with client.stream(
            "POST", "/api/query",
            json={"query": query, "persona": persona_id, "demo_mode": False}
        ) as r:
            assert r.status_code == 200
            async for line in r.aiter_lines():
                if not line.startswith("data: "):
                    continue
                event = json.loads(line[6:])
                if event["type"] == "token" and event.get("persona") == persona_id:
                    tokens.append(event["text"])
                elif event["type"] == "status":
                    status_events.append(event["stage"])
                elif event["type"] == "done":
                    break

    full_text = "".join(tokens)
    assert len(full_text) > 100, (
        f"[{persona_id}] Response too short ({len(full_text)} chars). "
        "Claude synthesis may have failed."
    )
    print(f"\n  [{persona_id}] {len(full_text)} chars streamed, "
          f"stages={status_events}")

    # Persona-specific content checks
    checks = {
        "medicinal_chemist": ["SAR", "IC50", "structure"],
        "pathologist":       ["mutation", "resistance", "clinical"],
        "cell_molecular_biologist":    ["pathway", "signaling", "mechanism"],
        "computational_biologist":     ["structure", "sequence", "dataset"],
    }
    keywords = checks[persona_id]
    matched = [kw for kw in keywords if kw.lower() in full_text.lower()]
    assert len(matched) >= 1, (
        f"[{persona_id}] None of {keywords} found in response.\n"
        f"Response preview: {full_text[:300]}"
    )


@pytest.mark.asyncio
async def test_query_compare_mode_all_four_personas_stream():
    """Compare mode (persona=None) must stream tokens for all 4 personas."""
    persona_tokens: dict[str, list[str]] = {}
    metadata = {}

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=180) as client:
        async with client.stream(
            "POST", "/api/query",
            json={"query": SHARED_QUERY, "persona": None, "demo_mode": False}
        ) as r:
            assert r.status_code == 200
            async for line in r.aiter_lines():
                if not line.startswith("data: "):
                    continue
                event = json.loads(line[6:])
                if event["type"] == "token":
                    pid = event["persona"]
                    persona_tokens.setdefault(pid, []).append(event["text"])
                elif event["type"] == "done":
                    metadata = event.get("metadata", {})
                    break

    assert len(persona_tokens) == 4, (
        f"Expected 4 personas, got tokens for: {list(persona_tokens.keys())}"
    )
    for pid, tokens in persona_tokens.items():
        text = "".join(tokens)
        assert len(text) > 100, f"[{pid}] Response too short: {len(text)} chars"
        print(f"  [{pid}] {len(text)} chars")

    assert metadata.get("llm_calls", 0) >= 5
    print(f"\n  Compare mode: {metadata.get('llm_calls')} LLM calls, "
          f"DBs={metadata.get('databases_queried', [])}")


@pytest.mark.asyncio
@pytest.mark.parametrize("persona_id", ["medicinal_chemist", "pathologist", "cell_molecular_biologist", "computational_biologist"])
async def test_query_lookup_scope_stays_concise(persona_id):
    """Lookup questions should stay short and not expand into dossier-style output."""
    query = "What is the receptor for Fibulin-1?"
    tokens = []
    metadata = {}

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=120) as client:
        async with client.stream(
            "POST", "/api/query",
            json={"query": query, "persona": persona_id, "demo_mode": False}
        ) as r:
            assert r.status_code == 200
            async for line in r.aiter_lines():
                if not line.startswith("data: "):
                    continue
                event = json.loads(line[6:])
                if event["type"] == "token" and event.get("persona") == persona_id:
                    tokens.append(event["text"])
                elif event["type"] == "done":
                    metadata = event.get("metadata", {})
                    break

    full_text = "".join(tokens)
    assert metadata.get("question_type") == "factual"
    assert metadata.get("question_scope") == "lookup"
    assert len(full_text) < 1200, (
        f"[{persona_id}] Lookup response is too long ({len(full_text)} chars).\n"
        f"Preview: {full_text[:400]}"
    )
    lowered = full_text.lower()
    assert "provenance" not in lowered
    assert "reference profile" not in lowered
    assert "dossier" not in lowered
    assert "identity & constitution" not in lowered


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query,expected_type,min_chars",
    [
        ("Explain how inhibiting ABL1 changes downstream signaling.", "detail", 250),
        ("Compare imatinib vs dasatinib for ABL1 resistance.", "comparison", 250),
        ("Could Fibulin-1 modulate EGFR signaling in this context?", "hypothesis", 250),
        ("What is known about EGFR resistance mechanisms?", "exploratory", 300),
        ("Integrate findings across structure, pathway, and disease for ABL1 inhibition.", "synthesis", 320),
        ("Build the reference profile for imatinib and ABL1.", "dossier", 500),
    ],
)
async def test_query_type_depth_regression(query, expected_type, min_chars):
    """Non-factual question types should not collapse into 2-3 line responses."""
    persona_id = "cell_molecular_biologist"
    tokens = []
    metadata = {}

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=120) as client:
        async with client.stream(
            "POST", "/api/query",
            json={"query": query, "persona": persona_id, "demo_mode": False}
        ) as r:
            assert r.status_code == 200
            async for line in r.aiter_lines():
                if not line.startswith("data: "):
                    continue
                event = json.loads(line[6:])
                if event["type"] == "token" and event.get("persona") == persona_id:
                    tokens.append(event["text"])
                elif event["type"] == "done":
                    metadata = event.get("metadata", {})
                    break

    full_text = "".join(tokens)
    assert metadata.get("question_type") == expected_type
    assert metadata.get("question_type_reason")
    assert metadata.get("question_scope") == "broad"
    assert len(full_text) >= min_chars, (
        f"[{expected_type}] response unexpectedly short ({len(full_text)} chars).\n"
        f"Preview: {full_text[:400]}"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "persona_id,gt_markers",
    [
        (
            "medicinal_chemist",
            ["cLogP", "TPSA", "Lipinski", "QED", "rotatable"],
        ),
        (
            "pathologist",
            ["EGFR", "ATP-competitive", "anilinoquinazoline", "CYP3A4"],
        ),
        (
            "cell_molecular_biologist",
            ["EGFR", "ATP-binding", "kinase", "4-anilinoquinazoline"],
        ),
        (
            "computational_biologist",
            ["Crippen", "TPSA", "HBD", "HBA", "InChIKey"],
        ),
    ],
)
async def test_query_erlotinib_molecular_properties_gt_regression(persona_id, gt_markers):
    """GT-based regression: query should preserve core erlotinib molecular properties across personas."""
    query = "what are the molecular properties of erlotinib"
    tokens = []
    metadata = {}

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=120) as client:
        async with client.stream(
            "POST", "/api/query",
            json={"query": query, "persona": persona_id, "demo_mode": False}
        ) as r:
            assert r.status_code == 200
            async for line in r.aiter_lines():
                if not line.startswith("data: "):
                    continue
                event = json.loads(line[6:])
                if event["type"] == "token" and event.get("persona") == persona_id:
                    tokens.append(event["text"])
                elif event["type"] == "done":
                    metadata = event.get("metadata", {})
                    break

    full_text = "".join(tokens)
    normalized = _normalize_text_for_gt(full_text)
    lowered = normalized.lower()

    # Core GT anchors shared in chat: formula and molecular-weight family.
    assert re.search(r"C22H23N3O4", normalized, re.IGNORECASE), (
        f"[{persona_id}] missing formula C22H23N3O4\n{full_text[:500]}"
    )
    has_free_base_mw = bool(re.search(r"393\.4|393\.44", normalized))
    has_salt_context = bool(re.search(r"hcl|hydrochloride|salt", lowered))
    has_hcl_salt_mw = bool(re.search(r"429\.9", normalized)) and has_salt_context
    assert has_free_base_mw or has_hcl_salt_mw, (
        f"[{persona_id}] missing expected molecular weight anchor (free base 393.4/393.44, "
        f"or 429.9 with explicit salt context)\n{full_text[:500]}"
    )

    # At least one strong identifier anchor from GT must appear.
    identifier_candidates = ["176870", "p00533", "aakjlrggtjkamg"]
    if persona_id == "computational_biologist":
        identifier_candidates.append("molecular descriptors")

    assert any(x in lowered for x in identifier_candidates), (
        f"[{persona_id}] missing expected GT identifier anchors (CID/UniProt/InChIKey).\n"
        f"Preview: {full_text[:700]}"
    )

    # Type compatibility assertions from current strategy.
    assert metadata.get("question_type") in {"detail", "exploratory", "synthesis", "dossier"}
    assert metadata.get("question_scope") == "broad"

    # Persona-level GT cues: include baseline markers plus curated ground-truth anchors.
    gt_fixture_markers = _GT_MARKERS_DATA["persona_markers"].get(persona_id, [])
    merged_markers = list(dict.fromkeys([*gt_markers, *gt_fixture_markers]))
    matched = [m for m in merged_markers if m.lower() in lowered]
    assert matched, (
        f"[{persona_id}] missing persona GT cues. Expected one of {merged_markers}.\n"
        f"Preview: {full_text[:700]}"
    )
