import base64
import binascii
import secrets

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL
import os
from pathlib import Path


def _load_env_dev():
    """Автоматически загружает env.dev файл из возможных местоположений."""
    BASE_DIR = Path(__file__).resolve().parent
    
    # Возможные пути к env.dev
    possible_paths = [
        BASE_DIR / "env.dev",  # backend/app/env.dev
        BASE_DIR.parent.parent / "env.dev",  # корень проекта
        BASE_DIR.parent / "env.dev",  # backend/env.dev
    ]
    
    for env_path in possible_paths:
        if env_path.exists() and env_path.is_file():
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        # Пропускаем пустые строки и комментарии
                        if not line or line.startswith('#'):
                            continue
                        # Парсим KEY=VALUE
                        if '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            # Убираем кавычки если есть
                            if value.startswith('"') and value.endswith('"'):
                                value = value[1:-1]
                            elif value.startswith("'") and value.endswith("'"):
                                value = value[1:-1]
                            # Устанавливаем переменную окружения только если она еще не установлена
                            if key and key not in os.environ:
                                os.environ[key] = value
                return
            except Exception:
                # Игнорируем ошибки чтения, пробуем следующий путь
                continue


# Загружаем env.dev автоматически при импорте модуля
_load_env_dev()


def _parse_secret_box_key(s: str) -> bytes:
    s = s.strip()
    try:
        b = base64.b64decode(s, validate=True)
        if len(b) == 32: return b
    except binascii.Error:
        pass
    try:
        b = bytes.fromhex(s)
        if len(b) == 32: return b
    except ValueError:
        pass
    raise ValueError("SECRET_BOX_KEY must be 32 bytes in Base64 or hex")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env", env_ignore_empty=True, extra="ignore"
    )

    DATABASE_URL: str = os.getenv("DATABASE_URL", URL.create(
        "postgresql+asyncpg",
        username="dbcv_test",
        password="dbcv_test",
        host="postgres",
        port=5433,
        database="dbcv_test",

    ).render_as_string(hide_password=False))
    BASE_DIR: Path = Path(__file__).resolve().parent

    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    SECRET_BOX_KEY: SecretStr | None = SecretStr(os.getenv("SECRET_BOX_KEY")) if os.getenv("SECRET_BOX_KEY") else None
    SECRET_BOX_KEY_FILE: str | None = os.getenv("SECRET_BOX_KEY_FILE")
    SECRET_BOX_KEY_DEFAULT_PATH: str = str(BASE_DIR / "secrets/secret_box_key")
    API_V1_STR: str = "/api/v1"
    FIRST_SUPERUSER: str = os.getenv("FIRST_SUPERUSER", "test")
    FIRST_SUPERUSER_PASSWORD: str = os.getenv("FIRST_SUPERUSER_PASSWORD", "test")
    EMAIL_TEST_USER: str = os.getenv("EMAIL_TEST_USER", "test.user@gmail.com")
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    # 60 minutes * 24 hours * 30 days = 30 days
    ANONYMOUS_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30
    PROJECT_NAME: str = "DBCV / ENI7"
    LOG_LEVEL: str = "DEBUG"
    MEDIA_URL: str = "media"
    STATIC_URL: str = "static"
    MEDIA_ROOT: Path = BASE_DIR / MEDIA_URL
    STATIC_ROOT: Path = BASE_DIR / STATIC_URL
    TEMPLATES_ROOT: Path = BASE_DIR / "templates"
    TIME_ZONE: str = "Europe/Moscow"

    MAX_LOG_SIZE: int = 4096

    # S3 storage
    S3_ENDPOINT: str = os.getenv("S3_ENDPOINT", "http://s3:9000")
    S3_PUBLIC_ENDPOINT: str = os.getenv("S3_PUBLIC_ENDPOINT", "http://localhost:9000")
    S3_REGION: str = os.getenv("S3_REGION", "ru")
    S3_ACCESS_KEY: str | None = os.getenv("S3_ACCESS_KEY")
    S3_SECRET_KEY: str | None = os.getenv("S3_SECRET_KEY")
    S3_BUCKET: str = os.getenv("S3_BUCKET", "dbcv-media")

    # broker streams
    USER_STREAM_NAME: str = "user_messages"
    BOT_STREAM_NAME: str = "bot_messages"
    USER_STREAM_GROUP: str = "user_group"
    BOT_STREAM_GROUP: str = "bot_group"
    EMITTER_STREAM_NAME: str = "emitters"
    EMITTER_STREAM_GROUP: str = "emitters_group"

    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", 10))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", 10))
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    CACHE_REDIS_URL: str = os.getenv("CACHE_REDIS_URL", "redis://cache-redis:6389/0")
    PROXIES: str = os.getenv("PROXIES", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    MCP_SERVICE_URL: str = os.getenv("MCP_SERVICE_URL", "http://mcp-dbcv:8005")
    MCP_HTTP_TIMEOUT: float = float(os.getenv("MCP_HTTP_TIMEOUT", "60"))
    MCP_SERVICE_TOKEN: str = os.getenv("MCP_SERVICE_TOKEN", "")

    @property
    def secret_box_key_bytes(self) -> bytes:
        if self.SECRET_BOX_KEY and self.SECRET_BOX_KEY.get_secret_value().strip():
            return _parse_secret_box_key(self.SECRET_BOX_KEY.get_secret_value())
        if self.SECRET_BOX_KEY_FILE and Path(self.SECRET_BOX_KEY_FILE).exists():
            return _parse_secret_box_key(Path(self.SECRET_BOX_KEY_FILE).read_text())
        p = Path(self.SECRET_BOX_KEY_DEFAULT_PATH)
        if p.exists():
            return _parse_secret_box_key(p.read_text())
        raise RuntimeError("SECRET_BOX_KEY not provided (env or file).")


settings = Settings()  # type: ignore

