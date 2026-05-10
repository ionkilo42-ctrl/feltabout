"""Internal emotional analysis schemas for staged extraction pipeline.

These schemas power the Feelings & Needs, Conflict Detection, Shame, and
Attachment engines. They are server-side only and NOT exposed to users.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ─── Enums ────────────────────────────────────────────────────────────────────

class EmotionCategory(str, Enum):
    """NVC-aligned emotion taxonomy."""
    FRUSTRATED = "frustrated"
    HURT = "hurt"
    ANGRY = "angry"
    SAD = "sad"
    ANXIOUS = "anxious"
    WORRIED = "worried"
    SCARED = "scared"
    ASHAMED = "ashamed"
    GUILTY = "guilty"
    DISAPPOINTED = "disappointed"
    CONFUSED = "confused"
    OVERWHELMED = "overwhelmed"
    EXHAUSTED = "exhausted"
    DISCONNECTED = "disconnected"
    UNHEARD = "unheard"
    UNSEEN = "unseen"
    DISMISSED = "dismissed"
    STUCK = "stuck"
    HOPEFUL = "hopeful"
    RELIEVED = "relieved"


class ConflictMarkerType(str, Enum):
    """Gottman Four Horsemen + related patterns."""
    CRITICISM = "criticism"
    CONTEMPT = "contempt"
    DEFENSIVENESS = "defensiveness"
    STONEWALLING = "stonewalling"
    FLOODING = "flooding"
    REPAIR_ATTEMPT = "repair_attempt"


class ShameType(str, Enum):
    """Brene Brown shame vs guilt distinction."""
    GUILT = "guilt"  # "I did something bad"
    SHAME = "shame"  # "I am bad"


class AttachmentFearType(str, Enum):
    """EFT attachment fears."""
    ABANDONMENT = "abandonment"
    REJECTION = "rejection"
    EMOTIONAL_DISCONNECTION = "emotional_disconnection"


class NervousSystemState(str, Enum):
    """Polyvagal states."""
    VENTRAL_VAGAL = "ventral_vagal"  # safe, connected
    SYMPATHETIC = "sympathetic"  # fight/flight
    DORSAL_VAGAL = "dorsal_vagal"  # collapse/disconnect


class MemoryCandidateReason(str, Enum):
    """Why this reflection qualifies as a Core Memory candidate."""
    HIGH_EMOTIONAL_INTENSITY = "high_emotional_intensity"
    RECURRING_THEME = "recurring_theme"
    SPECIFIC_PAST_EVENT = "specific_past_event"
    IDENTITY_WOUND = "identity_wound"
    RELATIONSHIP_RUPTURE = "relationship_rupture"
    UNRESOLVED_GRIEF = "unresolved_grief"
    FEAR_AFFECTS_CURRENT = "fear_affects_current"


class PrivacyLevel(str, Enum):
    """Core Memory privacy settings."""
    PRIVATE = "private"
    SHARED = "shared"


# ─── Emotion Signals ─────────────────────────────────────────────────────────

class EmotionSignal(BaseModel):
    """A detected emotion with intensity and source evidence."""
    name: EmotionCategory
    intensity: float  # 0.0 to 1.0
    source_text: str  # verbatim from user input


# ─── Needs Signals ────────────────────────────────────────────────────────────

class NeedCategory(str, Enum):
    """NVC-aligned needs inventory."""
    CONNECTION = "connection"
    AUTONOMY = "autonomy"
    RESPECT = "respect"
    UNDERSTANDING = "understanding"
    APPRECIATION = "appreciation"
    SECURITY = "security"
    TRUST = "trust"
    VALIDATION = "validation"
    SUPPORT = "support"
    SPACE = "space"
    CLARITY = "clarity"
    FAIRNESS = "fairness"
    GROWTH = "growth"
    MEANING = "meaning"
    PEACE = "peace"


class NeedSignal(BaseModel):
    """A detected need with intensity and source evidence."""
    category: NeedCategory
    text: str  # How user expressed this need
    intensity: float  # 0.0 to 1.0


# ─── Conflict Markers (Gottman) ───────────────────────────────────────────────

class ConflictMarker(BaseModel):
    """Detected conflict pattern from Gottman framework."""
    type: ConflictMarkerType
    evidence: str  # Text evidence from user input
    severity: float  # 0.0 to 1.0
    user_side: str  # "user" or "other"


# ─── Shame Markers (Brene Brown) ─────────────────────────────────────────────

class ShameMarker(BaseModel):
    """Detected shame vs guilt pattern."""
    shame_type: ShameType
    text_evidence: str
    underlying_fear: str
    is_hidden_anger: bool  # Is anger defending against shame?


# ─── Attachment Markers (EFT) ────────────────────────────────────────────────

class AttachmentMarker(BaseModel):
    """Detected attachment-related fear."""
    fear_type: AttachmentFearType
    text_evidence: str
    protest_behavior: Optional[str] = None  # e.g., "pursuing"
    withdrawal_behavior: Optional[str] = None  # e.g., "withdrawing"


# ─── Nervous System Markers (Polyvagal) ─────────────────────────────────────

class NervousSystemMarker(BaseModel):
    """Detected nervous system state."""
    state: NervousSystemState
    evidence: str
    is_overwhelmed: bool
    is_dysregulated: bool


# ─── Memory Candidates (IFS) ──────────────────────────────────────────────────

class MemoryCandidate(BaseModel):
    """A proposed Core Memory from reflection analysis."""
    title: str
    summary: str
    emotions: list[EmotionSignal]
    needs: list[NeedCategory]
    privacy_default: PrivacyLevel = PrivacyLevel.PRIVATE
    save_recommendation: bool
    reason: MemoryCandidateReason
    reason_text: str  # Human-readable explanation


# ─── Conversation Risks ─────────────────────────────────────────────────────────

class ConversationRisk(BaseModel):
    """Identified risk for the upcoming conversation."""
    risk_type: str  # "blame", "escalation", "shutdown", "manipulation"
    severity: float  # 0.0 to 1.0
    evidence: str
    recommendation: str  # What to avoid or do instead


# ─── Internal Analysis (Server-Side Only) ─────────────────────────────────────

class InternalAnalysis(BaseModel):
    """Complete internal analysis from staged extraction.

    This is server-side only. It is NOT exposed in API responses.
    It powers the conversation plan generation.
    """
    model_config = ConfigDict(from_attributes=True)

    # Primary extraction
    primary_emotions: list[EmotionSignal] = []
    secondary_emotions: list[EmotionSignal] = []
    needs: list[NeedSignal] = []
    values: list[str] = []  # ACT-aligned values present in reflection

    # Pattern detection
    conflict_markers: list[ConflictMarker] = []
    shame_markers: list[ShameMarker] = []
    attachment_markers: list[AttachmentMarker] = []
    nervous_system_markers: list[NervousSystemMarker] = []

    # Memory system
    memory_candidates: list[MemoryCandidate] = []

    # Conversation safety
    conversation_risks: list[ConversationRisk] = []

    # Metadata
    analysis_version: str = "mvp2_v1"
    extracted_at: Optional[datetime] = None

    def model_post_init(self, __context):
        if self.extracted_at is None:
            self.extracted_at = datetime.utcnow()

    @property
    def top_emotions(self) -> list[EmotionSignal]:
        """Return emotions sorted by intensity."""
        all_emotions = self.primary_emotions + self.secondary_emotions
        return sorted(all_emotions, key=lambda x: x.intensity, reverse=True)

    @property
    def emotion_distribution(self) -> dict[str, float]:
        """Simple emotion distribution for mobile display."""
        total = sum(e.intensity for e in self.top_emotions) or 1.0
        return {
            e.name.value: round(e.intensity / total * 100, 1)
            for e in self.top_emotions[:5]
        }

    @property
    def top_memory_candidate(self) -> Optional[MemoryCandidate]:
        """Return the highest-priority memory candidate."""
        if not self.memory_candidates:
            return None
        return max(self.memory_candidates, key=lambda x: x.save_recommendation)

    @property
    def has_shame(self) -> bool:
        """Check if shame patterns detected."""
        return any(m.shame_type == ShameType.SHAME for m in self.shame_markers)

    @property
    def has_escalation_risk(self) -> bool:
        """Check if high conversation risk detected."""
        return any(r.severity > 0.7 for r in self.conversation_risks)


# ─── User-Facing Memory Suggestion (Minimal) ──────────────────────────────────

class MemorySuggestion(BaseModel):
    """User-facing memory suggestion (minimal, no internal details)."""
    title: str
    summary: str
    reason: str  # "This seems like something worth remembering for future conversations."
    privacy_default: PrivacyLevel = PrivacyLevel.PRIVATE


# ─── Emotion Distribution (Mobile Display) ───────────────────────────────────

class EmotionDistributionItem(BaseModel):
    """Single emotion for mobile display."""
    name: str
    percentage: float
    intensity: float


class EmotionDistribution(BaseModel):
    """Emotion distribution for mobile display."""
    items: list[EmotionDistributionItem]
    dominant_emotion: str
    emotional_complexity: str  # "simple", "moderate", "complex"
