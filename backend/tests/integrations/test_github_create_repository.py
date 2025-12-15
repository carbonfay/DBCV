from pathlib import Path
import sys

# ВАЖНО: добавляем в sys.path директорию backend, где лежит пакет app
PROJECT_BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_BACKEND_ROOT))

from app.integrations.github.create_repository import (  # noqa: E402
    GitHubCreateRepositoryIntegration,
)


def test_github_create_repository_metadata_basic():
    integration = GitHubCreateRepositoryIntegration()
    meta = integration.metadata

    # Базовые поля
    assert meta.id == "github.create_repository"
    assert meta.version == "1.0.0"

    assert isinstance(meta.name, str) and meta.name.strip()
    assert isinstance(meta.description, str) and meta.description.strip()

    assert meta.category == "devtools"
    assert isinstance(meta.icon_s3_key, str) and meta.icon_s3_key.strip()
    assert isinstance(meta.color, str) and meta.color.startswith("#")

    # Схема конфига
    schema = meta.config_schema
    assert schema["type"] == "object"
    assert "name" in schema.get("required", [])
    assert "properties" in schema

    name_field = schema["properties"]["name"]
    assert name_field["type"] == "string"
