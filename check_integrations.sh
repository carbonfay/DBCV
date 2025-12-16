#!/bin/bash

# Скрипт для проверки интеграций Wildberries Get Product Info и Telegram Get Chat
# Шаг 5.4: Проверить код

echo "=== Проверка интеграций DBCV ==="
echo

# Проверка структуры файлов
echo "1. Проверка структуры файлов:"
echo

# Проверка Wildberries интеграции
echo "Wildberries Get Product Info:"
if [ -f "backend/app/integrations/wildberries/__init__.py" ]; then
    echo "✅ backend/app/integrations/wildberries/__init__.py существует"
else
    echo "❌ backend/app/integrations/wildberries/__init__.py отсутствует"
fi

if [ -f "backend/app/integrations/wildberries/get_product_info.py" ]; then
    echo "✅ backend/app/integrations/wildberries/get_product_info.py существует"
else
    echo "❌ backend/app/integrations/wildberries/get_product_info.py отсутствует"
fi

# Проверка Telegram Get Chat интеграции
echo
echo "Telegram Get Chat:"
if [ -f "backend/app/integrations/telegram/get_chat.py" ]; then
    echo "✅ backend/app/integrations/telegram/get_chat.py существует"
else
    echo "❌ backend/app/integrations/telegram/get_chat.py отсутствует"
fi

# Проверка импортов в __init__.py
echo
echo "Проверка импортов в backend/app/integrations/__init__.py:"
if grep -q "from app.integrations.wildberries import" backend/app/integrations/__init__.py; then
    echo "✅ Wildberries импорт найден"
else
    echo "❌ Wildberries импорт отсутствует"
fi

echo
echo "2. Проверка структуры классов:"
echo

# Проверка Wildberries интеграции
echo "Wildberries Get Product Info:"
if grep -q "class WildberriesGetProductInfoIntegration" backend/app/integrations/wildberries/get_product_info.py; then
    echo "✅ Класс WildberriesGetProductInfoIntegration найден"
else
    echo "❌ Класс WildberriesGetProductInfoIntegration отсутствует"
fi

if grep -q "BaseIntegration" backend/app/integrations/wildberries/get_product_info.py; then
    echo "✅ Наследование от BaseIntegration найдено"
else
    echo "❌ Наследование от BaseIntegration отсутствует"
fi

if grep -q "def execute" backend/app/integrations/wildberries/get_product_info.py; then
    echo "✅ Метод execute реализован"
else
    echo "❌ Метод execute отсутствует"
fi

# Проверка Telegram Get Chat интеграции
echo
echo "Telegram Get Chat:"
if grep -q "class TelegramGetChatIntegration" backend/app/integrations/telegram/get_chat.py; then
    echo "✅ Класс TelegramGetChatIntegration найден"
else
    echo "❌ Класс TelegramGetChatIntegration отсутствует"
fi

if grep -q "BaseIntegration" backend/app/integrations/telegram/get_chat.py; then
    echo "✅ Наследование от BaseIntegration найдено"
else
    echo "❌ Наследование от BaseIntegration отсутствует"
fi

if grep -q "def execute" backend/app/integrations/telegram/get_chat.py; then
    echo "✅ Метод execute реализован"
else
    echo "❌ Метод execute отсутствует"
fi

echo
echo "3. Проверка метаданных:"
echo

# Проверка метаданных Wildberries
echo "Wildberries Get Product Info метаданные:"
if grep -q "id=\"wildberries_get_product_info\"" backend/app/integrations/wildberries/get_product_info.py; then
    echo "✅ ID корректный"
else
    echo "❌ ID некорректный"
fi

if grep -q "name=\"Wildberries Get Product Info\"" backend/app/integrations/wildberries/get_product_info.py; then
    echo "✅ Название корректное"
else
    echo "❌ Название некорректное"
fi

if grep -q "category=\"ecommerce\"" backend/app/integrations/wildberries/get_product_info.py; then
    echo "✅ Категория корректная"
else
    echo "❌ Категория некорректная"
fi

# Проверка метаданных Telegram
echo
echo "Telegram Get Chat метаданные:"
if grep -q "id=\"telegram_get_chat\"" backend/app/integrations/telegram/get_chat.py; then
    echo "✅ ID корректный"
else
    echo "❌ ID некорректный"
fi

if grep -q "name=\"Telegram Get Chat\"" backend/app/integrations/telegram/get_chat.py; then
    echo "✅ Название корректное"
else
    echo "❌ Название некорректное"
fi

if grep -q "category=\"messaging\"" backend/app/integrations/telegram/get_chat.py; then
    echo "✅ Категория корректная"
else
    echo "❌ Категория некорректная"
fi

echo
echo "4. Проверка библиотек:"
echo

# Проверка SAFE_LIBRARIES.md
echo "Проверка SAFE_LIBRARIES.md:"
if grep -q "httpx" backend/app/integrations/SAFE_LIBRARIES.md; then
    echo "✅ httpx найден в SAFE_LIBRARIES.md"
else
    echo "❌ httpx отсутствует в SAFE_LIBRARIES.md"
fi

if grep -q "python-telegram-bot" backend/app/integrations/SAFE_LIBRARIES.md; then
    echo "✅ python-telegram-bot найден в SAFE_LIBRARIES.md"
else
    echo "❌ python-telegram-bot отсутствует в SAFE_LIBRARIES.md"
fi

# Проверка requirements
echo
echo "Проверка requirements:"
if grep -q "httpx" backend/requirements.txt; then
    echo "✅ httpx найден в requirements.txt"
else
    echo "❌ httpx отсутствует в requirements.txt"
fi

if grep -q "python-telegram-bot" backend/requirements.txt; then
    echo "✅ python-telegram-bot найден в requirements.txt"
else
    echo "❌ python-telegram-bot отсутствует в requirements.txt"
fi

echo
echo "5. Проверка credentials:"
echo

# Проверка credentials для Wildberries
echo "Wildberries credentials:"
if grep -q "credentials_provider=\"other\"" backend/app/integrations/wildberries/get_product_info.py; then
    echo "✅ credentials_provider корректный"
else
    echo "❌ credentials_provider некорректный"
fi

if grep -q "credentials_strategy=\"none\"" backend/app/integrations/wildberries/get_product_info.py; then
    echo "✅ credentials_strategy корректный"
else
    echo "❌ credentials_strategy некорректный"
fi

# Проверка credentials для Telegram
echo
echo "Telegram credentials:"
if grep -q "credentials_provider=\"telegram\"" backend/app/integrations/telegram/get_chat.py; then
    echo "✅ credentials_provider корректный"
else
    echo "❌ credentials_provider некорректный"
fi

if grep -q "credentials_strategy=\"api_key\"" backend/app/integrations/telegram/get_chat.py; then
    echo "✅ credentials_strategy корректный"
else
    echo "❌ credentials_strategy некорректный"
fi

echo
echo "6. Проверка обработки ошибок:"
echo

# Проверка try/except в Wildberries
echo "Wildberries обработка ошибок:"
if grep -q "try:" backend/app/integrations/wildberries/get_product_info.py && grep -q "except" backend/app/integrations/wildberries/get_product_info.py; then
    echo "✅ Try/except блоки присутствуют"
else
    echo "❌ Try/except блоки отсутствуют"
fi

if grep -q "await logger.error" backend/app/integrations/wildberries/get_product_info.py; then
    echo "✅ Логирование ошибок присутствует"
else
    echo "❌ Логирование ошибок отсутствует"
fi

# Проверка try/except в Telegram
echo
echo "Telegram обработка ошибок:"
if grep -q "try:" backend/app/integrations/telegram/get_chat.py && grep -q "except" backend/app/integrations/telegram/get_chat.py; then
    echo "✅ Try/except блоки присутствуют"
else
    echo "❌ Try/except блоки отсутствуют"
fi

if grep -q "await logger.error" backend/app/integrations/telegram/get_chat.py; then
    echo "✅ Логирование ошибок присутствует"
else
    echo "❌ Логирование ошибок отсутствует"
fi

echo
echo "=== Проверка завершена ==="
echo
echo "Если все пункты отмечены ✅, то интеграции реализованы корректно."
echo "Для полного тестирования запустите приложение и протестируйте интеграции в интерфейсе."