"""Initial schema — sessions, participants, utterances, safety_flags, escalations

Revision ID: 001_initial
Revises:
Create Date: 2026-05-06

"""
# type: ignore — alembic injects `op` as a runtime global
from typing import Sequence, Union

from alembic import op  # type: ignore
import sqlalchemy as sa  # type: ignore

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # sessions
    op.create_table(
        'sessions',
        sa.Column('session_id', sa.String(32), primary_key=True),
        sa.Column('mode', sa.String(32), default='facilitation'),
        sa.Column('last_speaker_id', sa.String(16), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    # participants
    op.create_table(
        'participants',
        sa.Column('id', sa.String(16), primary_key=True),
        sa.Column('session_id', sa.String(32), sa.ForeignKey('sessions.session_id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('role', sa.String(32), default='participant'),
        sa.Column('emotion', sa.String(32), default='neutral'),
        sa.Column('goals', sa.JSON(), nullable=True),
    )

    # utterances
    op.create_table(
        'utterances',
        sa.Column('id', sa.String(16), primary_key=True),
        sa.Column('session_id', sa.String(32), sa.ForeignKey('sessions.session_id', ondelete='CASCADE'), nullable=False),
        sa.Column('speaker_id', sa.String(16), nullable=False),
        sa.Column('speaker_name', sa.String(128), default=''),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('is_facilitator', sa.String(20), default='participant'),
    )
    op.create_index('ix_utterances_session_timestamp', 'utterances', ['session_id', 'timestamp'])

    # safety_flags
    op.create_table(
        'safety_flags',
        sa.Column('id', sa.String(16), primary_key=True),
        sa.Column('session_id', sa.String(32), sa.ForeignKey('sessions.session_id', ondelete='CASCADE'), nullable=False),
        sa.Column('level', sa.String(16), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('triggered_by', sa.String(16), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # escalations
    op.create_table(
        'escalations',
        sa.Column('id', sa.String(16), primary_key=True),
        sa.Column('session_id', sa.String(32), sa.ForeignKey('sessions.session_id', ondelete='CASCADE'), nullable=False),
        sa.Column('triggered_by', sa.String(16), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('status', sa.String(32), default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('escalations')
    op.drop_table('safety_flags')
    op.drop_table('utterances')
    op.drop_table('participants')
    op.drop_table('sessions')
