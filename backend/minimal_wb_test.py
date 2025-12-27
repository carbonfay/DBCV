"""Минимальный тест для проверки структуры интеграции Wildberries."""
import sys
import importlib.util
from pathlib import Path

print("="*60)
print("🔍 Minimal Wildberries Integration Structure Test")
print("="*60)
print()

# Путь к файлу интеграции
integration_file = Path(__file__).parent / "app" / "integrations" / "Wildberries" / "update_stock.py"

if not integration_file.exists():
    print(f"❌ Файл не найден: {integration_file}")
    sys.exit(1)

print(f"✅ Файл найден: {integration_file}")
print(f"   Размер: {integration_file.stat().st_size} bytes")
print()

# Читаем содержимое файла
with open(integration_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Проверяем ключевые элементы
print("🔍 Проверка содержимого:")

checks = [
    ("class WildberriesUpdateStockIntegration" in content, "Класс WildberriesUpdateStockIntegration"),
    ("BaseIntegration" in content, "Наследование от BaseIntegration"),
    ("def metadata" in content, "Метод metadata"),
    ("async def execute" in content, "Метод execute"),
    ('"wildberries_update_stock"' in content, "ID интеграции"),
    ("credentials_resolver" in content, "CredentialsResolver"),
    ("BotLogger" in content, "BotLogger"),
]

all_passed = True
for check, description in checks:
    status = "✅" if check else "❌"
    print(f"   {status} {description}")
    if not check:
        all_passed = False

print()

# Проверяем наличие библиотеки wildberries_api
print("📦 Проверка зависимостей:")
try:
    import wildberries_api
    print("   ✅ wildberries_api установлена")
except ImportError:
    print("   ⚠️  wildberries_api НЕ установлена (будет мок)")
    print("   Для установки: pip install wildberries-api")

print()

# Анализ метаданных из кода
print("📋 Метаданные интеграции (из исходного кода):")
import re

# Ищем метаданные
id_match = re.search(r'id="([^"]+)"', content)
version_match = re.search(r'version="([^"]+)"', content)
name_match = re.search(r'name="([^"]+)"', content)
category_match = re.search(r'category="([^"]+)"', content)

if id_match:
    print(f"   ID: {id_match.group(1)}")
if version_match:
    print(f"   Версия: {version_match.group(1)}")
if name_match:
    print(f"   Название: {name_match.group(1)}")
if category_match:
    print(f"   Категория: {category_match.group(1)}")

print()

if all_passed:
    print("✅ Все проверки пройдены!")
    print()
    print("📝 Структура интеграции корректна")
    print()
    print("Следующие шаги:")
    print("1. Убедитесь, что база данных запущена")
    print("2. Установите wildberries_api (если нужно): pip install wildberries-api")
    print("3. Добавьте credentials в БД")
    print("4. Запустите интеграцию через run_wildberries_integration.py")
else:
    print("❌ Некоторые проверки не прошли")
    print("   Проверьте структуру интеграции")

print()
print("="*60)
</contents>