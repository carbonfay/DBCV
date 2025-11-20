from alembic import op
import sqlalchemy as sa

# Идентификаторы ревизии
revision = "20250819_credentials_default_idx"
down_revision = "c7a29493ed79"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL partial unique index: один дефолт на (bot, provider, strategy)
    op.create_index(
        "uq_cred_default_per_provider",
        "credentials_entity",
        ["bot_id", "provider", "strategy"],
        unique=True,
        postgresql_where=sa.text("is_default = true"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_cred_default_per_provider",
        table_name="credentials_entity",
    )