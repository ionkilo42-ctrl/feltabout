"""
feltabout API — FastAPI backend for individual reflection and conversation-prep.

MVP scope: single-user reflection, no couples sessions, no realtime voice.

Architecture: Four-Engine Model
- Reflection Engine (app/services/reflection_service.py) — intake and emotional clarification
- Extraction Engine (app/services/extraction_service.py) — emotional analysis and core memory detection
- Facilitation Engine (app/services/facilitation_service.py) — reframing and conversation preparation
- Safety Engine (app/services/safety_service.py) — crisis, abuse, coercion, and escalation handling

All AI generation passes through Safety Engine first.
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

# ─── Config ───────────────────────────────────────────────────────────────────

_allowed_origins = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:3001,http://localhost:8081,http://localhost:8082"
).split(",")


# ─── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    from app.db.session import init_db
    await init_db()
    yield


# ─── FastAPI App ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="feltabout API",
    version="1.0.0",
    description=(
        "AI-guided reflection and conversation preparation for individuals. "
        "Not therapy, not crisis care — communication preparation and emotional clarity."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Include Routers ───────────────────────────────────────────────────────────

from app.api.routes_reflections import router as reflections_router
from app.api.routes_analytics import router as analytics_router
from app.api.routes_memories import router as memories_router
from app.api.routes_feelflow import router as feelflow_router
from app.api.routes_auth import router as auth_router
from app.api.routes_conversation_spaces import router as conversation_spaces_router
from app.api.routes_library import router as library_router
from app.api.routes_patterns import router as patterns_router

app.include_router(auth_router)
app.include_router(conversation_spaces_router)
app.include_router(reflections_router)
app.include_router(analytics_router)
app.include_router(memories_router)
app.include_router(feelflow_router)
app.include_router(library_router)
app.include_router(patterns_router)


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0.0", "service": "feltabout-api"}


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "feltabout API",
        "version": "1.0.0",
        "description": "AI-guided reflection and conversation preparation",
        "docs": "/docs",
        "health": "/health",
    }


# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
