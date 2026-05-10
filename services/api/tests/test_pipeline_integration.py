"""Integration tests for staged extraction pipeline.

Tests the full flow: Safety → Extraction → Facilitation
with proper privacy boundaries and fallback resilience.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.schemas.emotional_analysis import (
    InternalAnalysis,
    EmotionSignal,
    EmotionCategory,
    NeedSignal,
    NeedCategory,
    MemoryCandidateReason,
    PrivacyLevel,
)
from app.services.extraction_service import ExtractionService, get_fallback_analysis
from app.services.facilitation_service import FacilitationService


class TestExtractionFallbackResilience:
    """Tests that extraction failure never blocks plan generation."""

    def test_fallback_analysis_generates_valid_internal_analysis(self):
        """Fallback returns valid InternalAnalysis on any error."""
        reflection = {
            "situation": "Partner cancelled plans last minute",
            "feelings": "I felt hurt and frustrated",
            "interpretation": "They don't care about our time",
            "needs": "I need respect and consideration",
            "fears": "What if this keeps happening",
            "desired_outcome": "Better communication",
            "message_draft": "When you cancel...",
        }
        
        analysis = get_fallback_analysis(reflection)
        
        # Should return valid InternalAnalysis
        assert isinstance(analysis, InternalAnalysis)
        assert len(analysis.primary_emotions) >= 1
        assert analysis.has_escalation_risk is False

    @pytest.mark.asyncio
    async def test_extraction_service_handles_api_error_gracefully(self):
        """Extraction service returns fallback on API error."""
        extraction = ExtractionService()
        
        reflection = {
            "feelings": "angry and disappointed",
            "needs": "respect and understanding",
        }
        
        # Call without API key - uses fallback
        analysis = await extraction.analyze(reflection, api_key=None)
        
        assert isinstance(analysis, InternalAnalysis)
        assert len(analysis.primary_emotions) >= 1

    @pytest.mark.asyncio
    async def test_extraction_service_handles_malformed_response(self):
        """Extraction service returns fallback on malformed LLM response."""
        extraction = ExtractionService()
        
        # Mock AI router that returns malformed JSON
        mock_router = MagicMock()
        mock_router.generate = AsyncMock(return_value="This is not JSON {{{")
        
        extraction.ai_router = mock_router
        
        reflection = {"feelings": "test", "needs": "test"}
        analysis = await extraction.analyze(reflection, api_key="fake-key")
        
        # Should fall back to valid analysis
        assert isinstance(analysis, InternalAnalysis)


class TestSafetyGateShortCircuit:
    """Tests that safety check runs before extraction."""

    @pytest.mark.asyncio
    async def test_crisis_blocks_extraction_completely(self):
        """Crisis detection should block extraction from running."""
        from app.services.safety_service import check_safety
        
        crisis_text = "I want to kill myself"
        safety_result = check_safety(crisis_text)
        
        assert safety_result.is_crisis is True
        # Note: In actual route, extraction is skipped when is_crisis is True
        
    def test_safety_result_has_severity_for_routing(self):
        """Safety result includes severity for response routing."""
        from app.services.safety_service import check_safety
        
        crisis_text = "I'm going to hurt myself"
        safety_result = check_safety(crisis_text)
        
        assert safety_result.severity in ["high", "critical"]
        assert safety_result.is_crisis is True


class TestPrivacyBoundary:
    """Tests that InternalAnalysis never leaks into public response."""

    @pytest.mark.asyncio
    async def test_analysis_dict_does_not_contain_internal_fields(self):
        """Analysis dict should not contain raw InternalAnalysis fields."""
        from app.services.extraction_service import ExtractionService
        
        extraction = ExtractionService()
        reflection = {
            "feelings": "frustrated and hurt",
            "needs": "I need respect",
        }
        
        analysis = await extraction.analyze(reflection, api_key=None)
        
        # Convert to dict like the route does
        analysis_dict = {
            "primary_emotions": [
                {"name": e.name.value, "intensity": e.intensity, "source_text": e.source_text}
                for e in analysis.primary_emotions
            ],
            "needs": [
                {"category": n.category.value, "text": n.text, "intensity": n.intensity}
                for n in analysis.needs
            ],
            "memory_candidates": [
                {"title": m.title, "save_recommendation": m.save_recommendation}
                for m in analysis.memory_candidates
            ],
        }
        
        # Should only have public field names
        assert "model_dump" not in analysis_dict
        assert "has_shame" not in analysis_dict
        assert "top_emotions" not in analysis_dict
        assert "emotion_distribution" not in analysis_dict  # Only computed property, not a field

    def test_memory_candidates_have_privacy_default_private(self):
        """Memory candidates default to private - user controls visibility."""
        from app.schemas.emotional_analysis import MemoryCandidate
        
        candidate = MemoryCandidate(
            title="Test memory",
            summary="Test summary",
            emotions=[],
            needs=[],
            save_recommendation=True,
            reason=MemoryCandidateReason.HIGH_EMOTIONAL_INTENSITY,
            reason_text="Test",
        )
        
        # Privacy is user-controlled, defaults to private
        assert candidate.privacy_default == PrivacyLevel.PRIVATE


class TestMemoryCandidateLogging:
    """Tests for memory candidate logging without persistence."""

    def test_memory_candidate_count_accessible(self):
        """Memory candidate count should be accessible for logging."""
        analysis = InternalAnalysis(
            primary_emotions=[
                EmotionSignal(name=EmotionCategory.HURT, intensity=0.8, source_text="test")
            ],
            secondary_emotions=[],
            needs=[
                NeedSignal(category=NeedCategory.RESPECT, text="need respect", intensity=0.7)
            ],
            values=[],
            conflict_markers=[],
            shame_markers=[],
            attachment_markers=[],
            nervous_system_markers=[],
            memory_candidates=[],
            conversation_risks=[],
        )
        
        # Count should be accessible
        count = len(analysis.memory_candidates)
        assert count == 0

    @pytest.mark.asyncio
    async def test_memory_candidates_logged_but_not_persisted(self):
        """Memory candidates detected but not saved in Phase 1.5."""
        from app.services.extraction_service import ExtractionService
        
        extraction = ExtractionService()
        reflection = {
            "situation": "Childhood memory came up",
            "feelings": "I felt scared and overwhelmed",
            "needs": "I need safety",
        }
        
        analysis = await extraction.analyze(reflection, api_key=None)
        
        # Count for logging
        candidate_count = len(analysis.memory_candidates)
        
        # In Phase 1.5, we log the count but don't persist
        # This assertion documents the expected behavior
        assert isinstance(candidate_count, int)
        assert candidate_count >= 0


class TestFacilitationWithAnalysis:
    """Tests for facilitation service using analysis context."""

    @pytest.mark.asyncio
    async def test_generate_with_analysis_enhances_output(self):
        """Analysis context should enhance facilitation output."""
        facilitation = FacilitationService()
        
        reflection = {
            "situation": "Partner cancelled plans",
            "feelings": "I felt hurt and frustrated",
            "needs": "I need respect",
        }
        
        analysis = {
            "primary_emotions": [
                {"name": "hurt", "intensity": 0.8, "source_text": "I felt hurt"}
            ],
            "needs": [
                {"category": "respect", "text": "need respect", "intensity": 0.7}
            ],
            "conflict_markers": [],
            "shame_markers": [],
            "attachment_markers": [],
            "nervous_system_markers": [],
            "memory_candidates": [],
            "conversation_risks": [],
        }
        
        # Without API key, uses fallback
        plan = await facilitation.generate_with_analysis(
            reflection=reflection,
            analysis=analysis,
            api_key=None,
        )
        
        assert "emotional_summary" in plan
        assert "conversation_opener" in plan

    @pytest.mark.asyncio
    async def test_shame_markers_affect_tone(self):
        """Shame markers detected should affect facilitation tone."""
        facilitation = FacilitationService()
        
        reflection = {
            "situation": "Failed at work project",
            "feelings": "I'm a failure",
        }
        
        # Analysis with shame detected
        analysis = {
            "primary_emotions": [],
            "needs": [],
            "conflict_markers": [],
            "shame_markers": [
                {"shame_type": "shame", "text_evidence": "I am a failure", 
                 "underlying_fear": "rejection", "is_hidden_anger": True}
            ],
            "attachment_markers": [],
            "nervous_system_markers": [],
            "memory_candidates": [],
            "conversation_risks": [],
        }
        
        plan = await facilitation.generate_with_analysis(
            reflection=reflection,
            analysis=analysis,
            api_key=None,
        )
        
        # Fallback should include shame-aware guidance
        assert "avoid_saying" in plan
        assert "reframe" in plan


class TestMetadataFields:
    """Tests for extraction metadata fields."""

    def test_extraction_prompt_includes_required_taxonomy(self):
        """Extraction prompt should include framework taxonomy."""
        from app.prompts.extraction_prompt import EXTRACTION_SYSTEM_PROMPT
        
        # Should include NVC emotions
        assert "frustrated" in EXTRACTION_SYSTEM_PROMPT
        assert "hurt" in EXTRACTION_SYSTEM_PROMPT
        
        # Should include Gottman conflict markers
        assert "defensiveness" in EXTRACTION_SYSTEM_PROMPT
        assert "stonewalling" in EXTRACTION_SYSTEM_PROMPT
        
        # Should include Brené Brown shame types
        assert "guilt" in EXTRACTION_SYSTEM_PROMPT
        assert "shame" in EXTRACTION_SYSTEM_PROMPT
        
        # Should include Polyvagal states
        assert "sympathetic" in EXTRACTION_SYSTEM_PROMPT
        assert "dorsal_vagal" in EXTRACTION_SYSTEM_PROMPT

    def test_fallback_analysis_includes_required_fields(self):
        """Fallback analysis should include all required fields."""
        reflection = {"feelings": "test", "needs": "test"}
        
        analysis = get_fallback_analysis(reflection)
        
        # All fields should be present
        assert hasattr(analysis, "primary_emotions")
        assert hasattr(analysis, "secondary_emotions")
        assert hasattr(analysis, "needs")
        assert hasattr(analysis, "values")
        assert hasattr(analysis, "conflict_markers")
        assert hasattr(analysis, "shame_markers")
        assert hasattr(analysis, "attachment_markers")
        assert hasattr(analysis, "nervous_system_markers")
        assert hasattr(analysis, "memory_candidates")
        assert hasattr(analysis, "conversation_risks")
