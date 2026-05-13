"""
feltabout API — FastAPI backend for individual reflection and conversation-prep.

MVP scope: single-user reflection, no couples sessions, no realtime voice.

Architecture: Three-Engine Model
- Reflection Engine (app/services/reflection_service.py) — intake and emotional clarification
- Facilitation Engine (app/services/facilitation_service.py) — reframing and conversation preparation
- Safety Engine (app/services/safety_service.py) — escalation handling and guardrails

Extraction is an internal stage in the reflection pipeline, not a fourth product engine.
All AI generation passes through Safety Engine first.
"""

import os
import json
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

logger = logging.getLogger(__name__)

_allowed_origins = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:3001,http://localhost:8081,http://localhost:8082"
).split(",")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Validate runtime config and initialize database on startup."""
    from app.config_validation import validate_runtime_config
    from app.db.session import init_db

    validate_runtime_config()
    await init_db()
    yield


app = FastAPI(
    title="feltabout API",
    version="1.0.0",
    description=(
        "AI-guided reflection and conversation preparation for individuals. "
        "Communication preparation and emotional clarity."
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

from app.api.routes_reflections import router as reflections_router
from app.api.routes_analytics import router as analytics_router
from app.api.routes_memories import router as memories_router
from app.api.routes_feelflow import router as feelflow_router
from app.api.routes_auth import router as auth_router
from app.api.routes_conversation_spaces import router as conversation_spaces_router
from app.api.routes_session_messages import router as session_messages_router
from app.api.routes_library import router as library_router
from app.api.routes_patterns import router as patterns_router
from app.api.routes_v2 import memories_router, feelings_router, entities_router, needs_router, aimee_router
from app.api.routes_tts import router as tts_router

app.include_router(auth_router)
app.include_router(conversation_spaces_router)
app.include_router(session_messages_router)
app.include_router(reflections_router)
app.include_router(analytics_router)
app.include_router(memories_router)
app.include_router(feelflow_router)
app.include_router(library_router)
app.include_router(patterns_router)
app.include_router(tts_router)
app.include_router(feelings_router)
app.include_router(entities_router)
app.include_router(needs_router)
app.include_router(aimee_router)


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


@app.websocket("/ws/{session_id}")
async def websocket_stub(ws: WebSocket, session_id: str):
    """MVP 1 placeholder for future live sessions."""
    await ws.accept()
    welcome_message = {
        "type": "system",
        "content": (
            "This conversation space is ready, but live sessions are not enabled "
            "in this local MVP build yet. Your reflection and conversation "
            "preparation data has been saved. Full voice-facilitated sessions "
            "are planned for a later milestone."
        ),
        "session_id": session_id,
        "status": "placeholder",
    }
    await ws.send_json(welcome_message)
    logger.info(f"[WS Stub] Connection accepted for session: {session_id}")

    try:
        while True:
            data = await ws.receive_text()
            try:
                msg = json.loads(data)
                msg_type = msg.get("type", "unknown")
                ack = {
                    "type": "ack",
                    "original_type": msg_type,
                    "content": f"Received your message ({msg_type}). Live session features are planned for a later milestone.",
                    "session_id": session_id,
                }
                await ws.send_json(ack)
            except json.JSONDecodeError:
                ack = {
                    "type": "ack",
                    "content": "Message received. Live session features are planned for a later milestone.",
                    "session_id": session_id,
                }
                await ws.send_json(ack)
    except WebSocketDisconnect:
        logger.info(f"[WS Stub] Session {session_id} disconnected gracefully")
    except Exception as e:
        logger.warning(f"[WS Stub] Session {session_id} error: {e}")
        try:
            await ws.close(code=1011, reason="MVP 1 placeholder")
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
