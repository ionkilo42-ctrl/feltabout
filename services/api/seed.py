"""
Seed data script for feltabout — creates mock reflections for local testing.
Run with: python seed.py
Reset dev data first: python seed.py --reset
"""

import argparse
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/feltabout"
)

REFLECTIONS = [
    {
        "title": "Talk with my partner about division of chores",
        "situation": "We had a tense morning where I felt overwhelmed with chores while they seemed relaxed.",
        "feelings": "Frustrated, unheard, exhausted",
        "interpretation": "Maybe they don't care about sharing the load equally",
        "needs": "Support, recognition, partnership",
        "fears": "That they'll get defensive or shut down",
        "desired_outcome": "A fair division of tasks we both stick to",
        "message_draft": "Hey, can we talk about how we're dividing household tasks? I want to find something that works for both of us.",
    },
    {
        "title": "Hard conversation with my manager about feedback",
        "situation": "My manager gave vague feedback in our 1:1 that felt personal and left me confused.",
        "feelings": "Confused, undervalued, anxious",
        "interpretation": "They're dissatisfied with my work but won't say directly",
        "needs": "Clarity, respect, actionable guidance",
        "fears": "Losing my job or missing growth opportunities",
        "desired_outcome": "Specific, actionable feedback I can act on",
        "message_draft": "I'd like to discuss the feedback you gave — I want to make sure I understand what you're looking for.",
    },
    {
        "title": "Friend has been distant lately",
        "situation": "A close friend has been cancelling plans and responding slowly to messages.",
        "feelings": "Confused, hurt, worried",
        "interpretation": "Maybe they're upset with me about something",
        "needs": "Honest communication, reassurance",
        "fears": "Losing the friendship or having done something wrong",
        "desired_outcome": "To understand what's going on and restore our connection",
        "message_draft": "I've noticed we haven't been talking as much and I miss our time together. Is everything okay?",
    },
]


async def seed():
    parser = argparse.ArgumentParser(description="Seed feltabout local development data.")
    parser.add_argument("--reset", action="store_true", help="Delete dev-user reflections before inserting seed data.")
    args = parser.parse_args()

    from sqlalchemy import delete, select
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from app.models import Base, Reflection, ReflectionOutput, SafetyEvent, User
    from app.schemas.reflection import CreateReflectionRequest
    from app.services.reflection_service import ReflectionService

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Insert reflections
    async with async_session_factory() as session:
        user = User(
            id="dev-user-001",
            email="dev@feltabout.local",
            display_name="Dev User",
        )
        await session.merge(user)
        if args.reset:
            dev_reflection_ids = select(Reflection.id).where(Reflection.user_id == "dev-user-001")
            await session.execute(
                delete(ReflectionOutput).where(
                    ReflectionOutput.reflection_id.in_(dev_reflection_ids)
                )
            )
            await session.execute(
                delete(SafetyEvent).where(SafetyEvent.user_id == "dev-user-001")
            )
            await session.execute(
                delete(Reflection).where(Reflection.user_id == "dev-user-001")
            )
        for data in REFLECTIONS:
            await ReflectionService.create(
                session,
                "dev-user-001",
                CreateReflectionRequest(**data),
            )

    action = "Reset and seeded" if args.reset else "Seeded"
    print(f"{action} {len(REFLECTIONS)} reflections.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed())
