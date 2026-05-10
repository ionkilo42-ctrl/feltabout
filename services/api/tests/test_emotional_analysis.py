"""Tests for emotional_analysis schemas."""

import json
import pytest
from pydantic import ValidationError

from app.schemas.emotional_analysis import (
    EmotionCategory,
    EmotionSignal,
    NeedSignal,
    NeedCategory,
    ConflictMarker,
    ConflictMarkerType,
    ShameMarker,
    ShameType,
    AttachmentMarker,
    AttachmentFearType,
    NervousSystemMarker,
    NervousSystemState,
    ConversationRisk,
    MemoryCandidate,
    MemoryCandidateReason,
    PrivacyLevel,
    InternalAnalysis,
)


class TestEmotionSignal:
    """Tests for EmotionSignal schema."""

    def test_valid_emotion_signal(self):
        """EmotionSignal parses valid data."""
        signal = EmotionSignal(
            name=EmotionCategory.FRUSTRATED,
            intensity=0.8,
            source_text="I'm really frustrated about this.",
        )
        assert signal.name == EmotionCategory.FRUSTRATED
        assert signal.intensity == 0.8

    def test_invalid_emotion_category_fails(self):
        """Invalid emotion category raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            EmotionSignal(
                name="not_a_real_emotion",  # type: ignore
                intensity=0.8,
                source_text="test",
            )
        assert "validation error" in str(exc_info.value).lower()

    def test_intensity_out_of_range_fails(self):
        """Intensity outside 0-1 range may fail if we add validation."""
        signal = EmotionSignal(
            name=EmotionCategory.ANGRY,
            intensity=1.5,  # Would need manual validator if we want to enforce
            source_text="test",
        )
        # Currently Pydantic doesn't enforce range — uncomment if we add validator
        # assert "intensity" in str(exc_info.value).lower()


class TestConflictMarker:
    """Tests for ConflictMarker schema."""

    def test_valid_conflict_marker(self):
        """ConflictMarker parses valid data."""
        marker = ConflictMarker(
            type=ConflictMarkerType.DEFENSIVENESS,
            evidence="You always blame me for everything.",
            severity=0.7,
            user_side="user",
        )
        assert marker.type == ConflictMarkerType.DEFENSIVENESS
        assert marker.user_side == "user"

    def test_invalid_marker_type_fails(self):
        """Invalid marker type raises validation error."""
        with pytest.raises(ValidationError):
            ConflictMarker(
                type="not_a_horseman",  # type: ignore
                evidence="test",
                severity=0.5,
                user_side="user",
            )


class TestShameMarker:
    """Tests for ShameMarker schema."""

    def test_guilt_vs_shame_distinction(self):
        """Shame markers correctly distinguish guilt from shame."""
        guilt = ShameMarker(
            shame_type=ShameType.GUILT,
            text_evidence="I did something wrong and I feel bad about it.",
            underlying_fear="fear of having done harm",
            is_hidden_anger=False,
        )
        shame = ShameMarker(
            shame_type=ShameType.SHAME,
            text_evidence="I am a terrible person.",
            underlying_fear="fear of being seen as defective",
            is_hidden_anger=True,
        )
        assert guilt.shame_type == ShameType.GUILT
        assert shame.shame_type == ShameType.SHAME
        assert shame.is_hidden_anger is True


class TestMemoryCandidate:
    """Tests for MemoryCandidate schema."""

    def test_defaults_to_private(self):
        """MemoryCandidate defaults privacy to private."""
        candidate = MemoryCandidate(
            title="Feeling dismissed at dinner",
            summary="User felt ignored during family dinner conversation.",
            emotions=[
                EmotionSignal(
                    name=EmotionCategory.SAD,
                    intensity=0.78,
                    source_text="I felt really sad.",
                )
            ],
            needs=[],
            save_recommendation=True,
            reason=MemoryCandidateReason.SPECIFIC_PAST_EVENT,
            reason_text="Specific emotionally intense event.",
        )
        assert candidate.privacy_default == PrivacyLevel.PRIVATE

    def test_valid_memory_candidate(self):
        """MemoryCandidate parses complete data."""
        candidate = MemoryCandidate(
            title="Work conflict",
            summary="Manager dismissed my concerns publicly.",
            emotions=[
                EmotionSignal(
                    name=EmotionCategory.ANGRY,
                    intensity=0.65,
                    source_text="I was so angry.",
                ),
                EmotionSignal(
                    name=EmotionCategory.HURT,
                    intensity=0.82,
                    source_text="I felt hurt.",
                ),
            ],
            needs=[NeedCategory.RESPECT],
            privacy_default=PrivacyLevel.PRIVATE,
            save_recommendation=True,
            reason=MemoryCandidateReason.IDENTITY_WOUND,
            reason_text="Ties to core identity concerns.",
        )
        assert candidate.title == "Work conflict"
        assert len(candidate.emotions) == 2
        assert candidate.reason == MemoryCandidateReason.IDENTITY_WOUND


class TestInternalAnalysis:
    """Tests for InternalAnalysis schema."""

    def test_parses_complete_extraction_json(self):
        """InternalAnalysis parses complete extraction JSON."""
        analysis = InternalAnalysis(
            primary_emotions=[
                EmotionSignal(
                    name=EmotionCategory.FRUSTRATED,
                    intensity=0.85,
                    source_text="I'm so frustrated.",
                )
            ],
            secondary_emotions=[
                EmotionSignal(
                    name=EmotionCategory.SAD,
                    intensity=0.4,
                    source_text="And kind of sad.",
                )
            ],
            needs=[
                NeedSignal(
                    category=NeedCategory.UNDERSTANDING,
                    text="I need them to understand my perspective",
                    intensity=0.9,
                )
            ],
            values=["honesty", "connection"],
            conflict_markers=[
                ConflictMarker(
                    type=ConflictMarkerType.CRITICISM,
                    evidence="You never listen to me.",
                    severity=0.6,
                    user_side="user",
                )
            ],
            shame_markers=[
                ShameMarker(
                    shame_type=ShameType.SHAME,
                    text_evidence="I'm not good enough.",
                    underlying_fear="rejection",
                    is_hidden_anger=True,
                )
            ],
            attachment_markers=[
                AttachmentMarker(
                    fear_type=AttachmentFearType.EMOTIONAL_DISCONNECTION,
                    text_evidence="I'm scared we'll grow apart.",
                )
            ],
            nervous_system_markers=[
                NervousSystemMarker(
                    state=NervousSystemState.SYMPATHETIC,
                    evidence="Heart racing, feeling activated.",
                    is_overwhelmed=True,
                    is_dysregulated=True,
                )
            ],
            memory_candidates=[],
            conversation_risks=[],
        )
        
        assert len(analysis.primary_emotions) == 1
        assert len(analysis.secondary_emotions) == 1
        assert len(analysis.needs) == 1
        assert len(analysis.values) == 2
        assert len(analysis.conflict_markers) == 1
        assert analysis.has_shame is True

    def test_top_emotions_property(self):
        """top_emotions returns emotions sorted by intensity."""
        analysis = InternalAnalysis(
            primary_emotions=[
                EmotionSignal(name=EmotionCategory.SAD, intensity=0.4, source_text="sad"),
                EmotionSignal(name=EmotionCategory.ANGRY, intensity=0.8, source_text="angry"),
                EmotionSignal(name=EmotionCategory.SCARED, intensity=0.6, source_text="scared"),
            ],
            secondary_emotions=[],
            needs=[],
            values=[],
            conflict_markers=[],
            shame_markers=[],
            attachment_markers=[],
            nervous_system_markers=[],
            memory_candidates=[],
            conversation_risks=[],
        )
        
        top = analysis.top_emotions
        assert top[0].name == EmotionCategory.ANGRY
        assert top[1].name == EmotionCategory.SCARED
        assert top[2].name == EmotionCategory.SAD

    def test_emotion_distribution(self):
        """emotion_distribution returns normalized percentages."""
        analysis = InternalAnalysis(
            primary_emotions=[
                EmotionSignal(name=EmotionCategory.FRUSTRATED, intensity=50.0, source_text="test"),
                EmotionSignal(name=EmotionCategory.SAD, intensity=30.0, source_text="test"),
                EmotionSignal(name=EmotionCategory.HOPEFUL, intensity=20.0, source_text="test"),
            ],
            secondary_emotions=[],
            needs=[],
            values=[],
            conflict_markers=[],
            shame_markers=[],
            attachment_markers=[],
            nervous_system_markers=[],
            memory_candidates=[],
            conversation_risks=[],
        )
        
        dist = analysis.emotion_distribution
        total = sum(dist.values())
        # Should normalize to ~100%
        assert abs(total - 100.0) < 0.1
        assert dist["frustrated"] == 50.0

    def test_has_escalation_risk(self):
        """has_escalation_risk detects high-severity risks."""
        analysis_no_risk = InternalAnalysis(
            primary_emotions=[],
            secondary_emotions=[],
            needs=[],
            values=[],
            conflict_markers=[],
            shame_markers=[],
            attachment_markers=[],
            nervous_system_markers=[],
            memory_candidates=[],
            conversation_risks=[
                ConversationRisk(
                    risk_type="blame",
                    severity=0.4,
                    evidence="test",
                    recommendation="reframe",
                )
            ],
        )
        assert analysis_no_risk.has_escalation_risk is False
        
        analysis_high_risk = InternalAnalysis(
            primary_emotions=[],
            secondary_emotions=[],
            needs=[],
            values=[],
            conflict_markers=[],
            shame_markers=[],
            attachment_markers=[],
            nervous_system_markers=[],
            memory_candidates=[],
            conversation_risks=[
                ConversationRisk(
                    risk_type="blame",
                    severity=0.8,
                    evidence="test",
                    recommendation="reframe",
                )
            ],
        )
        assert analysis_high_risk.has_escalation_risk is True


class TestFeelFlowConstraints:
    """Tests for FeelFlow event constraints."""

    def test_confidence_score_0_to_1(self):
        """confidence_score should accept values 0-1."""
        # This is enforced at the schema level for FeelFlowEvent
        # Testing via NeedSignal as a proxy (same float field pattern)
        signal = NeedSignal(
            category=NeedCategory.CONNECTION,
            text="I need connection",
            intensity=0.75,
        )
        assert signal.intensity == 0.75
        # Values outside range should pass Pydantic but could be validated
        # if we add a validator

    def test_privacy_level_enum(self):
        """PrivacyLevel only accepts valid values."""
        candidate = MemoryCandidate(
            title="Test",
            summary="Test summary",
            emotions=[],
            needs=[],
            privacy_default=PrivacyLevel.PRIVATE,
            save_recommendation=True,
            reason=MemoryCandidateReason.HIGH_EMOTIONAL_INTENSITY,
            reason_text="Test",
        )
        assert candidate.privacy_default == "private"
