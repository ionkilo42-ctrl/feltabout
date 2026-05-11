"""V2 emotion graph models for feltabout.

This module contains the database models for the emotional graph:
- Feelings: individual emotional records
- Needs: need framework entries  
- Entities: people, topics, concepts feelings are about
- Topics: topic clusters
- Memories: saved emotional events with relationships
- Guides: AI guide personalities
- PublicAggregates: privacy-thresholded aggregations (internal only)
"""

from app.models.v2.base import Base
from app.models.v2.feeling import Feeling, FeelingNeed, feeling_needs, feeling_entities, feeling_topics
from app.models.v2.need import Need
from app.models.v2.entity import Entity, EntityType, PrivacyLevel
from app.models.v2.topic import Topic
from app.models.v2.memory import Memory, MemoryPrivacy
from app.models.v2.guide import Guide
from app.models.v2.aggregate import PublicEntityAggregate, TimeBucket

__all__ = [
    # Base
    "Base",
    # Enums
    "EntityType",
    "PrivacyLevel", 
    "MemoryPrivacy",
    "TimeBucket",
    # Association tables
    "feeling_needs",
    "feeling_entities",
    "feeling_topics",
    # Models
    "Feeling",
    "FeelingNeed",
    "Need",
    "Entity",
    "Topic",
    "Memory",
    "Guide",
    "PublicEntityAggregate",
]