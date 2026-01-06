"""empty message

Revision ID: 48afd6ad188c
Revises: 458db03e44d0
Create Date: 2025-08-13 09:45:44.591057

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bc5ad8ff984e'
down_revision = '48afd6ad188c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('channel', sa.Column('description', sa.String(), nullable=True))
    op.add_column('bot', sa.Column('description', sa.String(), nullable=True))


def downgrade():
    op.drop_column('channel', 'description')
    op.drop_column('bot', 'description')
