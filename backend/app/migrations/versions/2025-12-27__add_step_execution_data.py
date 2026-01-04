
"""add step_execution_data table

Revision ID: add_step_execution_data
Revises: add_integration_fields
Create Date: 2025-12-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON
import app.models.base


# revision identifiers, used by Alembic.
revision = 'add_step_execution_data'
down_revision = 'add_integration_fields'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'step_execution_data',
        sa.Column('id', app.models.base.UUID(), nullable=False),
        sa.Column('step_id', app.models.base.UUID(), nullable=False),
        sa.Column('user_id', app.models.base.UUID(), nullable=True),
        sa.Column('variables', JSON(), nullable=True),
        sa.Column('context', JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False),
        sa.ForeignKeyConstraint(['step_id'], ['step.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Создать уникальный индекс для step_id + user_id (только для записей с user_id)
    op.create_index(
        'uq_step_execution_data_step_user',
        'step_execution_data',
        ['step_id', 'user_id'],
        unique=True,
        postgresql_where=sa.text('user_id IS NOT NULL')
    )
    
    # Создать индекс для быстрого поиска по step_id
    op.create_index(
        'ix_step_execution_data_step_id',
        'step_execution_data',
        ['step_id']
    )


def downgrade():
    op.drop_index('ix_step_execution_data_step_id', table_name='step_execution_data')
    op.drop_index('uq_step_execution_data_step_user', table_name='step_execution_data')
    op.drop_table('step_execution_data')

