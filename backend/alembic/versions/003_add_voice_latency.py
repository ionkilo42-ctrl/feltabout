"""add_voice_latency_ms to facilitator_decisions

Revision ID: 003_add_voice_latency
Revises: 002_add_facilitator_decisions
Create Date: 2026-05-07
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "003_add_voice_latency"
down_revision = "002_add_facilitator_decisions"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "facilitator_decisions",
        sa.Column("voice_latency_ms", sa.Integer(), nullable=True),
    )
    op.add_column(
        "facilitator_decisions",
        sa.Column("is_voice_utterance", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade():
    op.drop_column("facilitator_decisions", "is_voice_utterance")
    op.drop_column("facilitator_decisions", "voice_latency_ms")