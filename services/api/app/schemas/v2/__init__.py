"""V2 schemas for feltabout API."""

from app.schemas.v2.feeling import (
    FeelingCreate,
    FeelingResponse,
    FeelingWithRelations,
)
from app.schemas.v2.need import (
    NeedResponse,
    NeedWithRelations,
)
from app.schemas.v2.entity import (
    EntityResponse,
    EntityWithRelations,
)
from app.schemas.v2.topic import (
    TopicResponse,
    TopicWithRelations,
)
from app.schemas.v2.memory import (
    CreateMemoryRequest,
    MemoryResponse,
    MemoryWithRelations,
    NestedMemoryResponse,
)
from app.schemas.v2.guide import (
    GuideCreate,
    GuideResponse,
)
from app.schemas.v2.feelflow import (
    FeelFlowQuery,
    FeelFlowResponse,
    FeelMapResponse,
)

__all__ = [
    # Feelings
    "FeelingCreate",
    "FeelingResponse",
    "FeelingWithRelations",
    # Needs
    "NeedResponse",
    "NeedWithRelations",
    # Entities
    "EntityResponse",
    "EntityWithRelations",
    # Topics
    "TopicResponse",
    "TopicWithRelations",
    # Memories
    "CreateMemoryRequest",
    "MemoryResponse",
    "MemoryWithRelations",
    "NestedMemoryResponse",
    # Guides
    "GuideCreate",
    "GuideResponse",
    # Analytics
    "FeelFlowQuery",
    "FeelFlowResponse",
    "FeelMapResponse",
]