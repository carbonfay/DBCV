"""empty message

Revision ID: 0892f4b83711
Revises: d2864a5cbda4
Create Date: 2025-01-11 18:55:49.593766

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '0892f4b83711'
down_revision = 'd1e28244d15d'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('step', sa.Column('timeout_after', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('step', 'timeout_after')
