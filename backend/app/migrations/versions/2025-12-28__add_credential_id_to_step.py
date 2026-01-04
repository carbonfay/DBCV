"""add credential_id to step

Revision ID: add_credential_id_to_step
Revises: add_step_execution_data
Create Date: 2025-12-28 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import app.models.base


# revision identifiers, used by Alembic.
revision = 'add_credential_id_to_step'
down_revision = 'add_step_execution_data'
branch_labels = None
depends_on = None


def upgrade():
    # Добавляем поле credential_id в таблицу step
    # Используем sa.UUID() для совместимости с credentials_entity.id (который использует нативный PostgreSQL UUID)
    op.add_column(
        'step',
        sa.Column(
            'credential_id',
            sa.UUID(),
            nullable=True
        )
    )
    
    # Добавляем внешний ключ с ondelete="SET NULL"
    op.create_foreign_key(
        'fk_step_credential_id_credentials_entity',
        'step',
        'credentials_entity',
        ['credential_id'],
        ['id'],
        ondelete='SET NULL'
    )
    
    # Создаем индекс для быстрого поиска по credential_id
    op.create_index(
        'ix_step_credential_id',
        'step',
        ['credential_id']
    )


def downgrade():
    # Удаляем индекс
    op.drop_index('ix_step_credential_id', table_name='step')
    
    # Удаляем внешний ключ
    op.drop_constraint('fk_step_credential_id_credentials_entity', 'step', type_='foreignkey')
    
    # Удаляем колонку
    op.drop_column('step', 'credential_id')

