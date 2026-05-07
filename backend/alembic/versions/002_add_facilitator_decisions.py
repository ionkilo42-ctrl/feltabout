"""add_facilitator_decisions

Revision ID: 002
Revises: 001_initial
Create Date: 2026-05-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = '002_add_facilitator_decisions'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'facilitator_decisions',
        sa.Column('id', sa.String(16), primary_key=True),
        sa.Column('session_id', sa.String(32), sa.ForeignKey('sessions.session_id', ondelete='CASCADE'), nullable=False),
        sa.Column('utterance_id', sa.String(16), nullable=True),
        sa.Column('timestamp', sa.DateTime, server_default=sa.func.now(), nullable=True),
        sa.Column('should_speak', sa.Boolean, nullable=False),
        sa.Column('intervention_type', sa.String(32), nullable=True),
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('trigger_reason', sa.String(128), nullable=True),
        sa.Column('latency_ms', sa.Integer, nullable=True),
        sa.Column('mode', sa.String(32), nullable=True),
        sa.Column('turn_phase', sa.String(32), nullable=True),
        sa.Column('conflict_pattern', sa.String(32), nullable=True),
    )
    op.create_index('ix_facilitator_decisions_session_id', 'facilitator_decisions', ['session_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_facilitator_decisions_session_id', table_name='facilitator_decisions')
    op.drop_table('facilitator_decisions')