"""PRISM — Persona-Driven Research Intelligence System
FastAPI backend with SSE streaming for 4-panel biomedical query responses.
"""
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

load_dotenv()

from orchestrator import run_pipeline, stream_pipeline
from entity_resolver import detect_persona

app = FastAPI(title="PRISM", version="1.0.0")

FRONTEND_DIR = Path(__file__).parent / "frontend"
PERSONAS_DIR = Path(__file__).parent / "personas"


# ── Request / Response models ─────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str
    persona: str | None = None   # None → compare all 4; set → single persona
    demo_mode: bool = False


class DetectRequest(BaseModel):
    query: str


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
async def serve_ui():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "PRISM"}


@app.get("/api/personas")
async def list_personas():
    """Return loaded persona metadata — shows extensibility to judges."""
    import yaml
    personas = []
    for f in sorted(PERSONAS_DIR.glob("*.yaml")):
        cfg = yaml.safe_load(f.read_text())
        personas.append({
            "id": f.stem,
            "name": cfg["name"],
            "emoji": cfg["emoji"],
            "sections": cfg["sections"],
            "connectors": [c["name"] for c in cfg["connectors"]],
        })
    return {"personas": personas}


@app.post("/api/detect-persona")
async def detect_persona_route(req: DetectRequest):
    """Infer user's professional role from their query language (Layer 2 auth)."""
    persona_id, confidence = await detect_persona(req.query)
    return {"persona_id": persona_id, "confidence": confidence}


@app.post("/api/query")
async def query_stream(req: QueryRequest):
    """
    SSE endpoint. Streams tokens as:
      data: {"type": "token",  "persona": "medicinal_chemist", "text": "..."}
      data: {"type": "status", "stage": "resolving", "message": "..."}
      data: {"type": "done",   "metadata": {...}}
    """
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not set")

    async def event_generator():
        async for event in stream_pipeline(
            query=req.query,
            persona=req.persona,
            demo_mode=req.demo_mode,
        ):
            yield {"data": json.dumps(event)}

    return EventSourceResponse(event_generator())


# ── Dev entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
