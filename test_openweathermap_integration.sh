#!/bin/bash

# Скрипт для тестирования OpenWeatherMap интеграции
# Использование: ./test_openweathermap_integration.sh [API_KEY]

API_KEY=${1:-"ВАШ_OPENWEATHERMAP_API_KEY"}

echo "🧪 Тестирование OpenWeatherMap интеграции"
echo "=========================================="

# 1. Получение токена
echo "1️⃣ Получение токена аутентификации..."
TOKEN=$(curl -s -X POST -F "username=test" -F "password=testtest" http://localhost:8003/api/v1/login/access-token | jq -r ".access_token")

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
    echo "❌ Ошибка: Не удалось получить токен"
    exit 1
fi

echo "✅ Токен получен"

# 2. Проверка каталога интеграций
echo ""
echo "2️⃣ Проверка каталога интеграций..."
INTEGRATION=$(curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8003/api/v1/integrations/catalog | jq '.items[] | select(.id == "openweathermap_daily_forecast")')

if [ -z "$INTEGRATION" ]; then
    echo "❌ Ошибка: Интеграция не найдена в каталоге"
    exit 1
fi

echo "✅ Интеграция найдена:"
echo "$INTEGRATION" | jq

# 3. Выполнение интеграции
echo ""
echo "3️⃣ Выполнение интеграции..."

if [ "$API_KEY" = "ВАШ_OPENWEATHERMAP_API_KEY" ]; then
    echo "⚠️  Внимание: Используется демо API ключ. Для реального тестирования:"
    echo "   1. Получите API ключ на https://openweathermap.org/api"
    echo "   2. Запустите скрипт с ключом: ./test_openweathermap_integration.sh YOUR_API_KEY"
    echo ""
    echo "📝 Структура запроса:"
    cat << 'EOF'
curl -X POST \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "integration_id": "openweathermap_daily_forecast",
    "config": {
      "latitude": 55.7558,
      "longitude": 37.6173,
      "units": "metric",
      "lang": "ru"
    },
    "credentials": {
      "api_key": "ВАШ_OPENWEATHERMAP_API_KEY"
    }
  }' \
  http://localhost:8003/api/v1/integrations/execute
EOF
    exit 0
fi

# Реальный запрос с API ключом
echo "🌤️ Выполнение запроса погоды для Москвы..."
RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"integration_id\": \"openweathermap_daily_forecast\", \"config\": {\"latitude\": 55.7558, \"longitude\": 37.6173, \"units\": \"metric\", \"lang\": \"ru\"}, \"credentials\": {\"api_key\": \"$API_KEY\"}}" \
  http://localhost:8003/api/v1/integrations/execute)

echo "📊 Результат:"
echo "$RESPONSE" | jq

# Проверка успешности
SUCCESS=$(echo "$RESPONSE" | jq -r '.ok')
if [ "$SUCCESS" = "true" ]; then
    echo ""
    echo "🎉 УСПЕХ! Интеграция работает корректно!"
    echo "Погода получена для: $(echo "$RESPONSE" | jq -r '.result.location.name')"
else
    echo ""
    echo "❌ Ошибка выполнения интеграции:"
    echo "Код ошибки: $(echo "$RESPONSE" | jq -r '.error_code')"
    echo "Описание: $(echo "$RESPONSE" | jq -r '.description')"
fi</content>
<parameter name="filePath">/Users/iton/Documents/MTI/1s/pracktise/DBCV/test_openweathermap_integration.sh