"""V2 API routes for emotional graph."""

from app.api.routes_v2.memories import router as memories_router
from app.api.routes_v2.feelings import router as feelings_router
from app.api.routes_v2.entities import router as entities_router
from app.api.routes_v2.needs import router as needs_router
from app.api.routes_v2.aimee import router as aimee_router

__all__ = [
    "memories_router",
    "feelings_router",
    "entities_router",
    "needs_router",
    "aimee_router",
]
