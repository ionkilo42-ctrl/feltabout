"""Entity model for emotional graph v2.

Entities are the people, topics, concepts, and things feelings are about.
They support private entities, connections, public figures, companies,
organizations, movements, concepts, events, and custom entities.
"""

from datetime import datetime
import uuid
import enum

from sqlalchemy import String, Text, DateTime, ForeignKey, Column, Boolean
from sqlalchemy.orm import relationship

from app.models.v2.base import Base
from app.models.v2.feeling import feeling_entities


class EntityType(str, enum.Enum):
    """Valid entity types."""
    PERSON = "person"
    SELF = "self"
    GUIDE = "guide"
    COMPANY = "company"
    ORGANIZATION = "organization"
    PUBLIC_FIGURE = "public_figure"
    MOVEMENT = "movement"
    CONCEPT = "concept"
    EVENT = "event"
    TOPIC = "topic"
    CONNECTION = "connection"
    CUSTOM = "custom"
    OTHER = "other"


class PrivacyLevel(str, enum.Enum):
    """Privacy levels for entities."""
    PRIVATE = "private"
    CONNECTIONS = "connections"
    PUBLIC = "public"


class Entity(Base):
    """An entity that feelings can be about."""
    __tablename__ = "v2_entities"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex[:16])
    canonical_name = Column(String(256), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    entity_type = Column(String(32), nullable=False, default=EntityType.PERSON.value)
    privacy_level = Column(String(32), nullable=False, default=PrivacyLevel.PRIVATE.value)
    is_connection = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    feelings = relationship("Feeling", secondary=feeling_entities, back_populates="entities")
    
    def __repr__(self):
        return f"<Entity {self.id}: {self.canonical_name} ({self.entity_type})>"