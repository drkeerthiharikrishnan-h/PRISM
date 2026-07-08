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
from users import list_users, get_user, PERSONA_LABELS, PERSONA_EMOJIS

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


class SwitchPersonaRequest(BaseModel):
    user_id: str
    new_persona: str


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
async def serve_ui():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "PRISM"}


# ── User endpoints ────────────────────────────────────────────────────────────

@app.get("/api/users")
async def get_users():
    """Return all demo researcher profiles for the login screen."""
    users = []
    for u in list_users():
        users.append({
            **u,
            "persona_label": PERSONA_LABELS.get(u["persona"], u["persona"]),
            "persona_emoji": PERSONA_EMOJIS.get(u["persona"], "🔬"),
        })
    return {"users": users}


@app.get("/api/users/{user_id}")
async def get_user_profile(user_id: str):
    """Return a single user profile + their assigned persona details."""
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
    return {
        **user,
        "persona_label": PERSONA_LABELS.get(user["persona"], user["persona"]),
        "persona_emoji": PERSONA_EMOJIS.get(user["persona"], "🔬"),
    }


@app.post("/api/users/{user_id}/switch-persona")
async def switch_persona(user_id: str, req: SwitchPersonaRequest):
    """
    Allow a user to override their default persona for the session.
    The override is remembered in the browser (sessionStorage) — not persisted server-side.
    """
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
    if req.new_persona not in PERSONA_LABELS:
        raise HTTPException(status_code=400, detail=f"Unknown persona '{req.new_persona}'")
    return {
        "user_id": user_id,
        "name": user["name"],
        "new_persona": req.new_persona,
        "persona_label": PERSONA_LABELS[req.new_persona],
        "persona_emoji": PERSONA_EMOJIS[req.new_persona],
        "message": f"Switched to {PERSONA_LABELS[req.new_persona]} view",
    }


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
