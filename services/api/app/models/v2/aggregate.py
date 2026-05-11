"""Public Entity Aggregate model for emotional graph v2.

This table stores privacy-thresholded aggregations of emotional data
about public entities. It is internal-only and not exposed via API.
"""

from datetime import datetime
import uuid
import enum

from sqlalchemy import String, Text, DateTime, Column, Float, Integer, Boolean
from sqlalchemy.orm import relationship

from app.models.v2.base import Base


class TimeBucket(str, enum.Enum):
    """Time granularity for aggregations."""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class PublicEntityAggregate(Base):
    """Aggregated emotional data about entities (internal only)."""
    __tablename__ = "v2_public_entity_aggregates"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex[:16])
    entity_id = Column(String(36), nullable=False, index=True)
    time_bucket = Column(String(32), nullable=False)
    bucket_start = Column(DateTime, nullable=False)
    bucket_end = Column(DateTime, nullable=False)
    primary_emotion = Column(String(32), nullable=False)
    need_name = Column(String(128), nullable=True)
    topic_cluster = Column(String(256), nullable=True)
    count = Column(Integer, default=0)
    avg_intensity = Column(Float, default=0.0)
    privacy_threshold_met = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<PublicEntityAggregate {self.id}: entity={self.entity_id} emotion={self.primary_emotion} count={self.count}>"