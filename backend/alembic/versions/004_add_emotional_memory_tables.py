"""add_core_memories_and_feel_flow_tables

Revision ID: 004_add_emotional_memory_tables
Revises: 003_add_voice_latency
Create Date: 2026-05-08
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "004_add_emotional_memory_tables"
down_revision = "003_add_voice_latency"
branch_labels = None
depends_on = None


def upgrade():
    # Create core_memories table
    op.create_table(
        "core_memories",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("summary", sa.Text(), server_default=""),
        sa.Column("emotions_json", sa.Text(), server_default="[]"),
        sa.Column("needs", sa.Text(), server_default="[]"),
        sa.Column("privacy", sa.String(16), server_default="private"),
        sa.Column("source_reflection_id", sa.String(36), sa.ForeignKey("reflections.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_confirmed", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_core_memories_user_id", "core_memories", ["user_id"])

    # Create feel_flow_events table
    op.create_table(
        "feel_flow_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reflection_id", sa.String(36), sa.ForeignKey("reflections.id", ondelete="CASCADE"), nullable=True),
        sa.Column("core_memory_id", sa.String(36), sa.ForeignKey("core_memories.id", ondelete="CASCADE"), nullable=True),
        sa.Column("emotion", sa.String(32), nullable=False),
        sa.Column("intensity", sa.Float(), nullable=False),
        sa.Column("source_text", sa.Text(), server_default=""),
        sa.Column("confidence_score", sa.Float(), server_default="0.0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_feel_flow_events_user_id", "feel_flow_events", ["user_id"])
    op.create_index("ix_feel_flow_events_reflection_id", "feel_flow_events", ["reflection_id"])
    op.create_index("ix_feel_flow_events_core_memory_id", "feel_flow_events", ["core_memory_id"])


def downgrade():
    op.drop_index("ix_feel_flow_events_core_memory_id", "feel_flow_events")
    op.drop_index("ix_feel_flow_events_reflection_id", "feel_flow_events")
    op.drop_index("ix_feel_flow_events_user_id", "feel_flow_events")
    op.drop_table("feel_flow_events")

    op.drop_index("ix_core_memories_user_id", "core_memories")
    op.drop_table("core_memories")
