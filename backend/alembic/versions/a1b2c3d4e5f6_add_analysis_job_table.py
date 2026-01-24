"""Add analysis_job table for status tracking

Revision ID: a1b2c3d4e5f6
Revises: 3e07e0c81ffa
Create Date: 2026-01-24 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '3e07e0c81ffa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create analysis_jobs table for tracking analysis status."""
    op.create_table(
        'analysis_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False, index=True),
        sa.Column('status', sa.String(50), nullable=False, default='PENDING'),
        sa.Column('current_step', sa.String(255), nullable=True),
        sa.Column('progress', sa.Integer(), nullable=False, default=0),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), nullable=True),
    )


def downgrade() -> None:
    """Drop analysis_jobs table."""
    op.drop_table('analysis_jobs')
