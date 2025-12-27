#!/usr/bin/env python3
"""Генератор безопасных ключей для env.prod файла.

Использование:
    python generate_secure_env.py
    
Этот скрипт:
1. Генерирует безопасные случайные ключи
2. Обновляет env.prod файл
3. Создает резервную копию старого файла
"""

import secrets
import base64
import os
import shutil
from datetime import datetime
from pathlib import Path


def generate_secret_key() -> str:
    """Генерирует SECRET_KEY (URL-safe base64)."""
    return secrets.token_urlsafe(32)


def generate_secret_box_key() -> str:
    """Генерирует SECRET_BOX_KEY (32 байта в base64)."""
    return base64.b64encode(secrets.token_bytes(32)).decode('utf-8')


def generate_password(length: int = 24) -> str:
    """Генерирует безопасный пароль."""
    alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_minio_credentials() -> tuple[str, str]:
    """Генерирует MinIO access key и secret key."""
    access_key = secrets.token_urlsafe(16)
    secret_key = secrets.token_urlsafe(32)
    return access_key, secret_key


def update_env_file(env_path: Path):
    """Обновляет env.prod файл с новыми ключами."""
    
    # Создаем резервную копию
    if env_path.exists():
        backup_path = env_path.with_suffix(f'.prod.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        shutil.copy2(env_path, backup_path)
        print(f"✅ Создана резервная копия: {backup_path.name}")
    
    # Читаем текущий файл
    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Генерируем новые ключи
    print("\n🔐 Генерация безопасных ключей...\n")
    
    secret_key = generate_secret_key()
    print(f"✅ SECRET_KEY: {secret_key[:20]}...")
    
    secret_box_key = generate_secret_box_key()
    print(f"✅ SECRET_BOX_KEY: {secret_box_key[:20]}...")
    
    db_password = generate_password()
    print(f"✅ Database Password: {db_password[:10]}...")
    
    minio_access, minio_secret = generate_minio_credentials()
    print(f"✅ MinIO Access Key: {minio_access}")
    print(f"✅ MinIO Secret Key: {minio_secret[:20]}...")
    
    admin_password = generate_password()
    print(f"✅ Admin Password: {admin_password[:10]}...")
    
    # Заменяем placeholder'ы
    replacements = {
        'SECRET_KEY=CHANGE_THIS_TO_RANDOM_SECRET_KEY_IN_PRODUCTION': f'SECRET_KEY={secret_key}',
        'SECRET_BOX_KEY=CHANGE_THIS_TO_BASE64_32_BYTES_KEY_IN_PRODUCTION=': f'SECRET_BOX_KEY={secret_box_key}',
        'POSTGRES_PASSWORD=CHANGE_DB_PASSWORD': f'POSTGRES_PASSWORD={db_password}',
        'DATABASE_URL=postgresql+asyncpg://dbcv_prod:CHANGE_DB_PASSWORD@postgres:5433/dbcv_prod': 
            f'DATABASE_URL=postgresql+asyncpg://dbcv_prod:{db_password}@postgres:5433/dbcv_prod',
        'S3_ACCESS_KEY=CHANGE_MINIO_ACCESS_KEY': f'S3_ACCESS_KEY={minio_access}',
        'S3_SECRET_KEY=CHANGE_MINIO_SECRET_KEY': f'S3_SECRET_KEY={minio_secret}',
        'MINIO_ROOT_USER=CHANGE_MINIO_ACCESS_KEY': f'MINIO_ROOT_USER={minio_access}',
        'MINIO_ROOT_PASSWORD=CHANGE_MINIO_SECRET_KEY': f'MINIO_ROOT_PASSWORD={minio_secret}',
        'FIRST_SUPERUSER_PASSWORD=CHANGE_ADMIN_PASSWORD': f'FIRST_SUPERUSER_PASSWORD={admin_password}',
    }
    
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    # Сохраняем обновленный файл
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✅ Файл {env_path.name} обновлен!\n")
    
    # Сохраняем credentials в отдельный файл для справки
    credentials_file = env_path.parent / 'PRODUCTION_CREDENTIALS.txt'
    with open(credentials_file, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("PRODUCTION CREDENTIALS - ХРАНИТЕ В БЕЗОПАСНОМ МЕСТЕ!\n")
        f.write("="*60 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("Database:\n")
        f.write(f"  User: dbcv_prod\n")
        f.write(f"  Password: {db_password}\n\n")
        f.write("MinIO/S3:\n")
        f.write(f"  Access Key: {minio_access}\n")
        f.write(f"  Secret Key: {minio_secret}\n\n")
        f.write("Admin User:\n")
        f.write(f"  Username: admin\n")
        f.write(f"  Password: {admin_password}\n\n")
        f.write("Security Keys:\n")
        f.write(f"  SECRET_KEY: {secret_key}\n")
        f.write(f"  SECRET_BOX_KEY: {secret_box_key}\n\n")
        f.write("="*60 + "\n")
        f.write("ВАЖНО:\n")
        f.write("1. Скопируйте эти credentials в безопасное хранилище\n")
        f.write("2. Удалите этот файл после копирования\n")
        f.write("3. Не коммитьте этот файл в git\n")
        f.write("="*60 + "\n")
    
    print(f"⚠️  ВАЖНО: Credentials сохранены в {credentials_file.name}")
    print("   Скопируйте их в безопасное место и УДАЛИТЕ файл!\n")
    
    return {
        'db_password': db_password,
        'minio_access': minio_access,
        'minio_secret': minio_secret,
        'admin_password': admin_password
    }


def main():
    """Главная функция."""
    print("="*60)
    print("🔐 Генератор безопасных ключей для DBCV")
    print("="*60)
    
    # Путь к env.prod
    env_path = Path(__file__).parent / 'env.prod'
    
    if not env_path.exists():
        print(f"\n❌ Файл {env_path.name} не найден!")
        print("   Создайте его сначала из env.example\n")
        return
    
    # Подтверждение
    print(f"\n📁 Файл для обновления: {env_path}")
    print("\n⚠️  ВНИМАНИЕ: Текущий файл будет изменен!")
    print("   Резервная копия будет создана автоматически.\n")
    
    response = input("Продолжить? (yes/no): ").strip().lower()
    if response not in ['yes', 'y', 'да']:
        print("\n❌ Отменено пользователем\n")
        return
    
    # Обновляем файл
    credentials = update_env_file(env_path)
    
    # Итоговые инструкции
    print("="*60)
    print("✅ Генерация завершена!")
    print("="*60)
    print("\nСледующие шаги:\n")
    print("1. Скопируйте credentials из PRODUCTION_CREDENTIALS.txt")
    print("2. Сохраните их в безопасном месте (password manager)")
    print("3. Удалите файл PRODUCTION_CREDENTIALS.txt")
    print("4. Проверьте env.prod файл")
    print("5. Запустите контейнеры: docker-compose up -d")
    print("\n" + "="*60 + "\n")


if __name__ == '__main__':
    main()
