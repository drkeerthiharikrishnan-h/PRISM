# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Facet (Persona-Driven Research Intelligence System) is a FastAPI biomedical research assistant that routes queries through four professional personas (medicinal chemist, pathologist, cell biologist, computational biologist). Each persona pulls data from open biomedical databases (PubMed, ChEMBL, PDB, UniProt, etc.) and synthesizes role-appropriate responses via Claude.

## Development Commands

```bash
# Install dependencies (uses uv lockfile)
uv sync

# Run development server (hot reload)
uv run uvicorn main:app --reload

# Run production server
uv run uvicorn main:app --host 0.0.0.0 --port 8000

# Docker
docker compose up --build

# Run all tests
uv run pytest tests/ -v

# Run backend tests only (no Playwright required)
uv run pytest tests/test_api.py tests/test_entity_resolver.py tests/test_connectors.py -v

# Run a single test
uv run pytest tests/test_api.py::test_personas_returns_all_four -v

# Run E2E tests (requires running server + Playwright browsers)
uv run pytest tests/e2e/ -v
```

**Required env vars** (in `.env`):
- `ANTHROPIC_API_KEY` — required
- `NCBI_API_KEY` — optional, raises PubMed rate limits

## Architecture

### 5-Step Query Pipeline

Every query flows through a fixed pipeline split across two modules:

**`entity_resolver.py` — Steps 1–2:**
1. **Parse query** (`parse_query()`) — 1 Haiku call; extracts `entity` (drug), `target` (protein/gene), `entity_type`; cached by query MD5 hash in `/cache/parse_*.json`
2. **Resolve IDs** (`resolve_ids()`) — pure HTTP; maps names → PubChem CID, ChEMBL ID, UniProt accession; returns `{entity, target, drug_pubchem, drug_chembl, target_uniprot, target_chembl}`

Also contains `guardrail_check()` — 1 Haiku call that validates biomedical relevance before the pipeline runs.

**`orchestrator.py` — Steps 3–5:**
3. **Persona planning** (`get_persona_plan()`) — reads persona YAML, extracts connector list; no LLM
4. **Parallel data retrieval** (`retrieve_for_persona()`) — calls 3–4 connectors per persona in parallel via `asyncio.gather()`
5. **Streaming synthesis** (`synthesize_stream()`) — 1 Sonnet 4.6 streaming call per persona; 4 sequential calls yielding SSE tokens

**LLM calls per query:** 1–2 Haiku (parse + guardrail) + 4 Sonnet 4.6 (synthesis) = 5–6 total.

### Persona & Connector Systems

Personas are defined in `/personas/*.yaml`. Each YAML specifies:
- `connectors`: list of which databases to query and with what params
- `sections`: output structure headers
- `synthesis_prompt`: role-specific system prompt for Claude

Connectors live in `/connectors/`. The `__init__.py` exports a `REGISTRY` dict mapping connector name strings → async fetch functions. All connectors share the same signature:
```python
async def fetch(entity_ids: dict, params: dict) -> dict
```
Personas reference connectors by name (from YAML), and the orchestrator looks them up in `REGISTRY` dynamically.

### Streaming (SSE)

`POST /api/query` returns an `EventSourceResponse`. Events are JSON-encoded with types:
- `{"type": "status", "stage": "parsing", "message": "..."}`
- `{"type": "token", "persona": "medicinal_chemist", "text": "..."}`
- `{"type": "done", "metadata": {...}}`

The frontend (`/frontend/index.html`) is a single-file vanilla JS SPA using the `EventSource` API. It renders 4 persona panels simultaneously as tokens stream in.

### Caching

Pre-fetched demo data lives in `/cache/`. Two levels:
- Parse cache: `parse_{md5}.json` — reuses entity extraction across runs
- Full pipeline cache: `{entity}_{target}.json` — 33 pre-populated files for demo (imatinib+ABL1, gefitinib+EGFR, etc.)

The cache bypasses live API calls for known queries, useful for testing without burning API quota.

### Users & Personas

Five hardcoded demo researchers in `users.py`, each pre-assigned a persona. No authentication — session stored in browser `sessionStorage`. `/api/detect-persona` can infer persona from query text (1 Haiku call).

## Key Files

| File | Role |
|------|------|
| `main.py` | FastAPI app, all route definitions |
| `orchestrator.py` | Pipeline steps 3–5 (planning, retrieval, synthesis) |
| `entity_resolver.py` | Pipeline steps 1–2 + guardrails |
| `users.py` | Demo researcher profiles |
| `personas/*.yaml` | Persona configs (connectors, prompts, sections) |
| `connectors/__init__.py` | `REGISTRY` mapping names → fetch functions |
| `frontend/index.html` | Entire frontend (single file, ~40KB) |
| `tests/conftest.py` | Shared test fixtures (BASE_URL, demo IDs) |

## Tech Stack

- **FastAPI** + **uvicorn** — backend
- **httpx** — async HTTP for all biomedical API calls
- **anthropic SDK** — Claude Haiku 4.5 (parse/guardrail), Claude Sonnet 4.6 (synthesis)
- **sse-starlette** — Server-Sent Events streaming
- **uv** — dependency management (use `uv run` prefix, not `python`)
- **pytest** + **pytest-asyncio** (asyncio_mode = "auto") + **pytest-playwright** — testing
