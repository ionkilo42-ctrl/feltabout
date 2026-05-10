"""User model for feltabout."""

from datetime import datetime
import uuid

from sqlalchemy import String, DateTime, Column
from sqlalchemy.orm import relationship

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex[:16])
    email = Column(String(256), unique=True, nullable=False, index=True)
    display_name = Column(String(128), nullable=False)
    password_hash = Column(String(256), nullable=True)  # null = magic link only, set = password auth
    created_at = Column(DateTime, default=datetime.utcnow)

    reflections = relationship("Reflection", back_populates="user", cascade="all, delete-orphan")
    core_memories = relationship("CoreMemory", back_populates="user", cascade="all, delete-orphan")
    feel_flow_events = relationship("FeelFlowEvent", back_populates="user", cascade="all, delete-orphan")
