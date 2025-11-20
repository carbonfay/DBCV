"""add integration fields to connection_group

Revision ID: add_integration_fields
Revises: 468d32916b7b
Create Date: 2025-11-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = 'add_integration_fields'
down_revision = '468d32916b7b'  # Последняя миграция на момент создания
branch_labels = None
depends_on = None


def upgrade():
    # Добавляем поля для интеграций
    op.add_column('connection_group', sa.Column('integration_id', sa.String(), nullable=True))
    op.add_column('connection_group', sa.Column('integration_config', JSON, nullable=True))
    
    # Добавляем новый тип в enum SearchType
    # В PostgreSQL нужно использовать ALTER TYPE для добавления значения
    op.execute("ALTER TYPE searchtype ADD VALUE IF NOT EXISTS 'integration'")


def downgrade():
    # Удаляем поля
    op.drop_column('connection_group', 'integration_config')
    op.drop_column('connection_group', 'integration_id')
    
    # Примечание: удаление значения из enum в PostgreSQL сложно,
    # поэтому оставляем значение 'integration' в enum

