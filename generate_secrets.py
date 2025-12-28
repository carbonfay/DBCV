#!/usr/bin/env python3
"""Генератор безопасных секретных ключей для env.prod."""

import secrets
import base64
import string


def generate_secret_key(length: int = 32) -> str:
    """Генерирует URL-безопасный секретный ключ."""
    return secrets.token_urlsafe(length)


def generate_secret_box_key() -> str:
    """Генерирует 32-байтовый ключ в base64 для NaCl SecretBox."""
    key_bytes = secrets.token_bytes(32)
    return base64.b64encode(key_bytes).decode('utf-8')


def generate_password(length: int = 24) -> str:
    """Генерирует сложный пароль."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def generate_minio_credentials() -> tuple[str, str]:
    """Генерирует credentials для MinIO (минимум 3 символа)."""
    access_key = 'minio_' + secrets.token_urlsafe(12)
    secret_key = secrets.token_urlsafe(32)
    return access_key, secret_key


def main():
    print("="*60)
    print("🔐 DBCV Secret Keys Generator")
    print("="*60)
    print()
    
    print("Генерация секретных ключей...")
    print()
    
    # Генерируем все ключи
    secret_key = generate_secret_key()
    secret_box_key = generate_secret_box_key()
    db_password = generate_password()
    admin_password = generate_password()
    minio_access, minio_secret = generate_minio_credentials()
    
    # Выводим результаты
    print("📋 Скопируйте эти значения в ваш env.prod файл:")
    print()
    
    print("# Core Security")
    print(f"SECRET_KEY={secret_key}")
    print(f"SECRET_BOX_KEY={secret_box_key}")
    print()
    
    print("# Database")
    print(f"POSTGRES_PASSWORD={db_password}")
    print(f"DATABASE_URL=postgresql+asyncpg://dbcv_prod:{db_password}@postgres:5433/dbcv_prod")
    print()
    
    print("# MinIO / S3")
    print(f"MINIO_ROOT_USER={minio_access}")
    print(f"MINIO_ROOT_PASSWORD={minio_secret}")
    print(f"S3_ACCESS_KEY={minio_access}")
    print(f"S3_SECRET_KEY={minio_secret}")
    print()
    
    print("# Admin User")
    print(f"FIRST_SUPERUSER_PASSWORD={admin_password}")
    print()
    
    print("="*60)
    print("⚠️  ВАЖНО: Сохраните эти ключи в безопасном месте!")
    print("="*60)
    print()
    
    # Опционально: автоматическое обновление env.prod
    response = input("Автоматически обновить env.prod? (y/N): ").strip().lower()
    
    if response == 'y':
        try:
            # Читаем текущий env.prod
            with open('env.prod', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Заменяем плейсхолдеры
            replacements = {
                'CHANGE_THIS_TO_RANDOM_SECRET_KEY_IN_PRODUCTION': secret_key,
                'CHANGE_THIS_TO_BASE64_32_BYTES_KEY_IN_PRODUCTION': secret_box_key,
                'CHANGE_DB_PASSWORD': db_password,
                'CHANGE_MINIO_ACCESS_KEY': minio_access,
                'CHANGE_MINIO_SECRET_KEY': minio_secret,
                'CHANGE_ADMIN_PASSWORD': admin_password,
            }
            
            for old, new in replacements.items():
                content = content.replace(old, new)
            
            # Сохраняем обновленный файл
            with open('env.prod', 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ Файл env.prod обновлен!")
            print()
            
        except Exception as e:
            print(f"❌ Ошибка при обновлении файла: {e}")
            print("Скопируйте значения вручную.")
    else:
        print("ℹ️  Скопируйте значения вручную в env.prod")


if __name__ == "__main__":
    main()
