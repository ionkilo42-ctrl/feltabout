"""
Reflection Service — Business logic for reflection CRUD operations.

This is the Reflection Engine in feltabout's three-engine architecture.
Handles all reflection-related business logic, separate from routes and database models.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Reflection, ReflectionOutput, ReflectionFeedback, User
from app.schemas.reflection import (
    CreateReflectionRequest,
    UpdateReflectionRequest,
    CreateFeedbackRequest,
    UpdateFeedbackRequest,
)
from app.services.encryption_service import get_encryption_service


# ─── Sensitive fields to encrypt/decrypt ───────────────────────────────────────

# Reflection input fields that hold deeply personal content
REFLECTION_SENSITIVE_FIELDS = [
    "situation",
    "feelings",
    "interpretation",
    "needs",
    "fears",
    "desired_outcome",
    "message_draft",
]

# ReflectionOutput fields that contain generated personal guidance
OUTPUT_SENSITIVE_FIELDS = [
    "emotional_summary",
    "needs_summary",
    "assumptions",
    "reframe",
    "avoid_saying",
    "conversation_opener",
    "followup_questions",
    "repair_statement",
]


def _encrypt_fields(data: dict) -> dict:
    """Encrypt sensitive string fields in a dict, in-place."""
    enc = get_encryption_service()
    for field in REFLECTION_SENSITIVE_FIELDS:
        if field in data and data[field]:
            data[field] = enc.encrypt(str(data[field]))
    return data


def _decrypt_reflection(reflection: Reflection) -> None:
    """Decrypt sensitive fields on a Reflection object in-place."""
    enc = get_encryption_service()
    for field in REFLECTION_SENSITIVE_FIELDS:
        value = getattr(reflection, field, None)
        if value:
            setattr(reflection, field, enc.decrypt(value))


def _decrypt_output(output: ReflectionOutput) -> None:
    """Decrypt sensitive fields on a ReflectionOutput object in-place."""
    enc = get_encryption_service()
    for field in OUTPUT_SENSITIVE_FIELDS:
        value = getattr(output, field, None)
        if value:
            setattr(output, field, enc.decrypt(value))


def _encrypt_output_fields(plan_data: dict) -> dict:
    """Encrypt sensitive fields in a plan_data dict, returns new dict."""
    enc = get_encryption_service()
    result = dict(plan_data)
    for field in OUTPUT_SENSITIVE_FIELDS:
        if field in result and result[field]:
            result[field] = enc.encrypt(str(result[field]))
    return result


class ReflectionService:
    """
    Reflection Engine for feltabout.
    
    Responsible for:
    - Creating new reflections
    - Fetching user reflections (with output eager-loaded)
    - Updating reflection fields
    - Deleting reflections
    - Managing reflection status
    - Saving/retrieving feedback
    """
    
    @staticmethod
    async def ensure_user(db: AsyncSession, user: dict) -> User:
        """
        Ensure the current auth identity has a database row.
        
        Args:
            db: Database session
            user: User dict with 'sub' (id), 'email', 'name'
            
        Returns:
            User record
        """
        result = await db.execute(select(User).where(User.id == user["sub"]))
        existing = result.scalar_one_or_none()
        if existing:
            return existing
        
        record = User(
            id=user["sub"],
            email=user.get("email") or f"{user['sub']}@feltabout.local",
            display_name=user.get("name") or "Feltabout User",
        )
        db.add(record)
        await db.commit()
        return record
    
    @staticmethod
    async def create(db: AsyncSession, user_id: str, data: CreateReflectionRequest) -> Reflection:
        """
        Create a new reflection.

        Args:
            db: Database session
            user_id: User ID
            data: CreateReflectionRequest with reflection fields

        Returns:
            Created Reflection
        """
        # Encrypt sensitive input fields before storing
        enc_data = _encrypt_fields(data.model_dump())

        reflection = Reflection(
            user_id=user_id,
            title=enc_data.get("title", ""),
            situation=enc_data.get("situation", ""),
            feelings=enc_data.get("feelings", ""),
            interpretation=enc_data.get("interpretation", ""),
            needs=enc_data.get("needs", ""),
            fears=enc_data.get("fears", ""),
            desired_outcome=enc_data.get("desired_outcome", ""),
            message_draft=enc_data.get("message_draft", ""),
        )
        db.add(reflection)
        await db.commit()
        await db.refresh(reflection)
        return reflection
    
    @staticmethod
    async def list_by_user(db: AsyncSession, user_id: str) -> list[Reflection]:
        """
        List all reflections for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of Reflection objects (with output eager-loaded)
            — sensitive fields are decrypted before return
        """
        result = await db.execute(
            select(Reflection)
            .options(selectinload(Reflection.output))
            .where(Reflection.user_id == user_id)
            .order_by(Reflection.created_at.desc())
        )
        reflections = list(result.scalars().all())
        # Decrypt sensitive fields before returning to API
        for r in reflections:
            _decrypt_reflection(r)
            if r.output:
                _decrypt_output(r.output)
        return reflections
    
    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        reflection_id: str,
        user_id: str,
    ) -> Optional[Reflection]:
        """
        Get a specific reflection by ID.

        Args:
            db: Database session
            reflection_id: Reflection ID
            user_id: User ID (for authorization)

        Returns:
            Reflection or None if not found — sensitive fields are decrypted
        """
        result = await db.execute(
            select(Reflection)
            .options(selectinload(Reflection.output))
            .where(
                Reflection.id == reflection_id,
                Reflection.user_id == user_id,
            )
        )
        reflection = result.scalar_one_or_none()
        if reflection:
            _decrypt_reflection(reflection)
            if reflection.output:
                _decrypt_output(reflection.output)
        return reflection
    
    @staticmethod
    async def update(
        db: AsyncSession,
        reflection: Reflection,
        data: UpdateReflectionRequest,
    ) -> Reflection:
        """
        Update reflection fields.

        Args:
            db: Database session
            reflection: Reflection to update
            data: UpdateReflectionRequest with fields to update

        Returns:
            Updated Reflection
        """
        update_data = data.model_dump(exclude_unset=True)
        # Encrypt sensitive fields before storing
        update_data = _encrypt_fields(update_data)
        for field, value in update_data.items():
            if value is not None:
                setattr(reflection, field, value)

        await db.commit()
        await db.refresh(reflection)
        return reflection
    
    @staticmethod
    async def delete(db: AsyncSession, reflection: Reflection) -> None:
        """
        Delete a reflection.
        
        Args:
            db: Database session
            reflection: Reflection to delete
        """
        await db.delete(reflection)
        await db.commit()
    
    @staticmethod
    async def save_output(
        db: AsyncSession,
        reflection: Reflection,
        plan_data: dict,
        metadata: dict | None = None,
    ) -> ReflectionOutput:
        """
        Save or update the conversation plan output for a reflection.

        Args:
            db: Database session
            reflection: Reflection to save output for
            plan_data: Dict with conversation plan fields
            metadata: Optional dict with generation metadata (prompt_version, model_provider, etc.)

        Returns:
            Created/updated ReflectionOutput
        """
        # Encrypt sensitive output fields before storing
        enc_plan = _encrypt_output_fields(plan_data)

        output = reflection.output or ReflectionOutput(reflection_id=reflection.id)
        output.emotional_summary = enc_plan.get("emotional_summary", "")
        output.needs_summary = enc_plan.get("needs_summary", "")
        output.assumptions = enc_plan.get("assumptions", "")
        output.reframe = enc_plan.get("reframe", "")
        output.avoid_saying = enc_plan.get("avoid_saying", "")
        output.conversation_opener = enc_plan.get("conversation_opener", "")
        output.followup_questions = enc_plan.get("followup_questions", "")
        output.repair_statement = enc_plan.get("repair_statement", "")
        
        # Apply generation metadata if provided
        if metadata:
            output.prompt_version = metadata.get("prompt_version", output.prompt_version)
            output.model_provider = metadata.get("model_provider", output.model_provider)
            output.model_name = metadata.get("model_name", output.model_name)
            output.generation_mode = metadata.get("generation_mode", output.generation_mode)
            output.safety_version = metadata.get("safety_version", output.safety_version)
        
        db.add(output)
        
        # Mark reflection as completed
        reflection.status = "completed"
        
        await db.commit()
        await db.refresh(output)
        return output
    
    @staticmethod
    async def save_feedback(
        db: AsyncSession,
        reflection_id: str,
        user_id: str,
        data: CreateFeedbackRequest,
    ) -> ReflectionFeedback:
        """
        Save feedback for a reflection.
        
        Args:
            db: Database session
            reflection_id: Reflection ID
            user_id: User ID
            data: CreateFeedbackRequest with scores and optional text
            
        Returns:
            Created ReflectionFeedback
        """
        # Check if feedback already exists (one feedback per reflection)
        result = await db.execute(
            select(ReflectionFeedback).where(ReflectionFeedback.reflection_id == reflection_id)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing feedback
            existing.prepared_score = data.prepared_score
            existing.less_reactive_score = data.less_reactive_score
            existing.helpful_text = data.helpful_text
            db.add(existing)
            await db.commit()
            await db.refresh(existing)
            return existing
        
        # Create new feedback
        feedback = ReflectionFeedback(
            reflection_id=reflection_id,
            user_id=user_id,
            prepared_score=data.prepared_score,
            less_reactive_score=data.less_reactive_score,
            helpful_text=data.helpful_text,
        )
        db.add(feedback)
        await db.commit()
        await db.refresh(feedback)
        return feedback
    
    @staticmethod
    async def get_feedback(
        db: AsyncSession,
        reflection_id: str,
        user_id: str,
    ) -> Optional[ReflectionFeedback]:
        """
        Get feedback for a reflection.
        
        Args:
            db: Database session
            reflection_id: Reflection ID
            user_id: User ID (for authorization)
            
        Returns:
            ReflectionFeedback or None
        """
        result = await db.execute(
            select(ReflectionFeedback).where(
                ReflectionFeedback.reflection_id == reflection_id,
                ReflectionFeedback.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_feedback(
        db: AsyncSession,
        feedback: ReflectionFeedback,
        data: UpdateFeedbackRequest,
    ) -> ReflectionFeedback:
        """
        Update feedback fields — used for the follow-up question.
        
        Args:
            db: Database session
            feedback: ReflectionFeedback to update
            data: UpdateFeedbackRequest with fields to update
            
        Returns:
            Updated ReflectionFeedback
        """
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(feedback, field, value)
        
        await db.commit()
        await db.refresh(feedback)
        return feedback
    
    @staticmethod
    def get_reflection_text(reflection: Reflection) -> str:
        """
        Get all reflection text combined for safety checking.
        
        Args:
            reflection: Reflection object
            
        Returns:
            Combined text of all reflection fields
        """
        return " ".join([
            reflection.situation or "",
            reflection.feelings or "",
            reflection.interpretation or "",
            reflection.needs or "",
            reflection.fears or "",
            reflection.desired_outcome or "",
            reflection.message_draft or "",
        ])
