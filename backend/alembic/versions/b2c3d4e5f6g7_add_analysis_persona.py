"""Add analysis_persona columns for polymorphic analysis

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-25 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add analysis_persona columns to users, analysis_jobs, and analysis_reports tables."""
    # Add analysis_persona to users table (default: INVESTOR)
    op.add_column(
        'users',
        sa.Column('analysis_persona', sa.String(50), nullable=False, server_default='INVESTOR')
    )

    # Add analysis_persona to analysis_jobs table
    op.add_column(
        'analysis_jobs',
        sa.Column('analysis_persona', sa.String(50), nullable=True)
    )

    # Add analysis_persona and analysis_focus_area to analysis_reports table
    op.add_column(
        'analysis_reports',
        sa.Column('analysis_persona', sa.String(50), nullable=True)
    )
    op.add_column(
        'analysis_reports',
        sa.Column('analysis_focus_area', postgresql.JSON(), nullable=True, server_default='{}')
    )


def downgrade() -> None:
    """Remove analysis_persona columns."""
    op.drop_column('analysis_reports', 'analysis_focus_area')
    op.drop_column('analysis_reports', 'analysis_persona')
    op.drop_column('analysis_jobs', 'analysis_persona')
    op.drop_column('users', 'analysis_persona')
