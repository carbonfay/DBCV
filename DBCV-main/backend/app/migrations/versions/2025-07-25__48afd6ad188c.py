"""empty message

Revision ID: 48afd6ad188c
Revises: 458db03e44d0
Create Date: 2025-07-25 09:45:44.591057

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '48afd6ad188c'
down_revision = '458db03e44d0'
branch_labels = None
depends_on = None


# Имя типа в БД
enum_name = "requestmethodtype"


def upgrade():
    op.execute("ALTER TYPE {} ADD VALUE IF NOT EXISTS 'put'".format(enum_name))
    op.execute("ALTER TYPE {} ADD VALUE IF NOT EXISTS 'delete'".format(enum_name))
    op.execute("ALTER TYPE {} ADD VALUE IF NOT EXISTS 'patch'".format(enum_name))


def downgrade():
    # Downgrade для ENUM в PostgreSQL не поддерживается напрямую.
    pass