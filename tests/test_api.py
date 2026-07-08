"""
Backend tests — FastAPI endpoints via httpx async client.
Server must be running: uv run uvicorn main:app --port 8000

Run:  uv run pytest tests/test_api.py -v
"""
import json
import pytest
import httpx
from tests.conftest import BASE_URL, PERSONA_QUERIES, SHARED_QUERY


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
    assert data["service"] == "PRISM"


@pytest.mark.asyncio
async def test_ui_serves_html(client):
    r = await client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "PRISM" in r.text


# ── Personas endpoint ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_personas_returns_all_four(client):
    r = await client.get("/api/personas")
    assert r.status_code == 200
    data = r.json()
    assert "personas" in data
    assert len(data["personas"]) == 4

    ids = {p["id"] for p in data["personas"]}
    assert ids == {"medicinal_chemist", "pathologist", "cell_biologist", "comp_biologist"}


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
                                         "cell_biologist", "comp_biologist"])
async def test_query_single_persona_streams_tokens(persona_id):
    """Each persona should produce streaming tokens with persona-specific content."""
    tokens = []
    status_events = []

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=120) as client:
        async with client.stream(
            "POST", "/api/query",
            json={"query": SHARED_QUERY, "persona": persona_id, "demo_mode": False}
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
        "cell_biologist":    ["pathway", "signaling", "mechanism"],
        "comp_biologist":    ["structure", "sequence", "dataset"],
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
