# Руководство по использованию OpenWeatherMap Daily Forecast Integration

## 🚀 Быстрый старт

### 1. Регистрация интеграции

```python
from app.integrations.weather import OpenWeatherMapDailyForecastIntegration
from app.integrations.registry import IntegrationRegistry

# Создайте реестр
registry = IntegrationRegistry()

# Зарегистрируйте интеграцию
integration = OpenWeatherMapDailyForecastIntegration()
registry.register(integration)
```

### 2. Использование интеграции

```python
# Получите интеграцию из реестра
integration = registry.get("openweathermap_daily_forecast", "1.0.0")

# Вызовите метод execute
result = await integration.execute(
    config={
        "latitude": 55.7558,
        "longitude": 37.6173,
        "units": "metric",
        "lang": "ru"
    },
    credentials_resolver=credentials_resolver,
    bot_id=bot_id,
    logger=logger
)

# Обработайте результат
if result["response"]["ok"]:
    weather = result["response"]["result"]
    print(f"Город: {weather['location']['name']}")
    print(f"Температура: {weather['current_weather']['temperature']}°C")
else:
    error = result["response"]["description"]
    print(f"Ошибка: {error}")
```

## 📝 Подробное описание

### Параметры execute()

| Параметр | Тип | Описание | Пример |
|----------|-----|---------|--------|
| config | Dict[str, Any] | Конфигурация интеграции | `{"latitude": 55.7558, "longitude": 37.6173}` |
| credentials_resolver | CredentialsResolver | Резолвер для получения credentials | resolver |
| bot_id | UUID | ID бота для логирования и credentials | `uuid4()` |
| logger | BotLogger | Логгер для записи событий | logger |

### Config параметры

#### Обязательные

**latitude** (number)
- Широта местоположения
- Диапазон: -90 до 90
- Пример: 55.7558 (Москва)

**longitude** (number)
- Долгота местоположения
- Диапазон: -180 до 180
- Пример: 37.6173 (Москва)

#### Опциональные

**units** (string, по умолчанию: "metric")
- Единицы измерения
- Допустимые значения:
  - `"metric"` - Celsius, м/с (по умолчанию)
  - `"imperial"` - Fahrenheit, миль/ч
  - `"standard"` - Kelvin, м/с
- Пример: `"metric"`

**lang** (string, по умолчанию: "en")
- Язык описания погоды
- Допустимые значения: "en", "ru", "fr", "de", "es", "ja", "zh_cn" и другие
- Пример: `"ru"`

## 💾 Формат ответа

### Успешный ответ (ok: true)

```python
{
    "response": {
        "ok": True,
        "result": {
            "location": {
                "name": "Moscow",           # Название города
                "country": "RU",           # Код страны
                "latitude": 55.7558,       # Широта
                "longitude": 37.6173,      # Долгота
                "timezone": 10800          # Offset в секундах от UTC
            },
            "current_weather": {
                "temperature": -5.2,       # Текущая температура
                "feels_like": -12.5,       # Ощущаемая температура
                "temp_min": -8.1,          # Минимальная температура
                "temp_max": -2.3,          # Максимальная температура
                "pressure": 1013,          # Давление в hPa
                "humidity": 75,            # Влажность в %
                "visibility": 10000,       # Видимость в метрах
                "wind_speed": 5.5,         # Скорость ветра
                "wind_degree": 230,        # Направление ветра в градусах
                "wind_gust": null,         # Порывы ветра (если есть)
                "cloudiness": 90,          # Облачность в %
                "description": "overcast clouds",  # Описание
                "main": "Clouds",          # Основное состояние
                "icon": "04d"              # Код иконки OpenWeatherMap
            },
            "units": "metric",             # Использованные единицы
            "timestamp": 1639086600,       # Unix timestamp времени данных
            "sunrise": 1639071600,         # Unix timestamp восхода
            "sunset": 1639101300           # Unix timestamp заката
        }
    }
}
```

### Ошибка (ok: false)

```python
{
    "response": {
        "ok": False,
        "error_code": 401,                 # HTTP код ошибки
        "description": "Invalid API key"   # Описание ошибки
    }
}
```

## 🔍 Коды ошибок

| Код | Название | Причина |
|-----|----------|---------|
| 400 | Bad Request | Недействительные параметры (latitude/longitude вне диапазона) |
| 401 | Unauthorized | API ключ не найден или недействителен |
| 404 | Not Found | Город/координаты не найдены в OpenWeatherMap |
| 500 | Internal Server Error | Непредвиденная ошибка (сеть, парсинг и т.д.) |

## 📚 Примеры использования

### Пример 1: Простой запрос погоды для Москвы

```python
result = await integration.execute(
    config={
        "latitude": 55.7558,
        "longitude": 37.6173
    },
    credentials_resolver=credentials_resolver,
    bot_id=bot_id,
    logger=logger
)

if result["response"]["ok"]:
    location = result["response"]["result"]["location"]
    weather = result["response"]["result"]["current_weather"]
    
    print(f"{location['name']}, {location['country']}")
    print(f"Температура: {weather['temperature']}°C")
    print(f"Состояние: {weather['description']}")
```

### Пример 2: Запрос с заданными единицами

```python
result = await integration.execute(
    config={
        "latitude": 40.7128,
        "longitude": -74.0060,
        "units": "imperial",
        "lang": "en"
    },
    credentials_resolver=credentials_resolver,
    bot_id=bot_id,
    logger=logger
)

if result["response"]["ok"]:
    weather = result["response"]["result"]["current_weather"]
    print(f"Temperature: {weather['temperature']}°F")
```

### Пример 3: Обработка ошибок

```python
result = await integration.execute(
    config={
        "latitude": 55.7558,
        "longitude": 37.6173
    },
    credentials_resolver=credentials_resolver,
    bot_id=bot_id,
    logger=logger
)

if not result["response"]["ok"]:
    error_code = result["response"]["error_code"]
    error_msg = result["response"]["description"]
    
    if error_code == 401:
        print("Ошибка: API ключ не настроен")
    elif error_code == 400:
        print(f"Ошибка: Недействительные параметры - {error_msg}")
    elif error_code == 404:
        print(f"Ошибка: Местоположение не найдено - {error_msg}")
    else:
        print(f"Ошибка: {error_code} - {error_msg}")
else:
    # Обработка успешного результата
    pass
```

### Пример 4: Запрос погоды на русском языке

```python
result = await integration.execute(
    config={
        "latitude": 55.7558,
        "longitude": 37.6173,
        "units": "metric",
        "lang": "ru"
    },
    credentials_resolver=credentials_resolver,
    bot_id=bot_id,
    logger=logger
)

if result["response"]["ok"]:
    location = result["response"]["result"]["location"]
    weather = result["response"]["result"]["current_weather"]
    
    message = f"""
    📍 {location['name']}, {location['country']}
    🌡️ Температура: {weather['temperature']}°C (ощущается как {weather['feels_like']}°C)
    ☁️ Состояние: {weather['description'].capitalize()}
    💨 Ветер: {weather['wind_speed']} м/с
    💧 Влажность: {weather['humidity']}%
    """
    print(message)
```

## ⚙️ Настройка credentials

### Создание credentials для OpenWeatherMap

1. Зарегистрируйтесь на https://openweathermap.org/api
2. Получите API ключ на https://openweathermap.org/api
3. Сохраните API ключ в CredentialEntity с:
   - **provider**: "openweathermap"
   - **strategy**: "api_key"
   - **payload**: `{"api_key": "your-api-key-here"}`

### Пример создания credentials (в коде)

```python
from app.models.credentials import CredentialEntity

credential = CredentialEntity(
    bot_id=bot_id,
    provider="openweathermap",
    strategy="api_key",
    payload_encrypted=encrypt({"api_key": "your-openweathermap-api-key"})
)

await db.add(credential)
await db.commit()
```

## 🧪 Тестирование

### Запуск тестов

```bash
cd backend
python -m pytest app/integrations/weather/test_openweathermap_daily_forecast.py -v
```

### Запуск конкретного теста

```bash
python -m pytest app/integrations/weather/test_openweathermap_daily_forecast.py::TestOpenWeatherMapDailyForecastIntegration::test_metadata_structure -v
```

## 📊 Примеры данных OpenWeatherMap

### Описания погоды (main)
- Clear
- Clouds
- Drizzle
- Rain
- Thunderstorm
- Snow
- Mist

### Иконки
- 01d/01n - Ясно (день/ночь)
- 02d/02n - Переменная облачность (день/ночь)
- 03d/03n - Облачно (день/ночь)
- 04d/04n - Пасмурно
- 09d/09n - Морось (день/ночь)
- 10d/10n - Дождь (день/ночь)
- 11d/11n - Гроза (день/ночь)
- 13d/13n - Снег (день/ночь)
- 50d/50n - Туман (день/ночь)

## 🔗 Дополнительные ресурсы

- OpenWeatherMap API документация: https://openweathermap.org/api
- OpenWeatherMap Weather API: https://openweathermap.org/weather-3d
- Список городов: https://openweathermap.org/find
- Коды языков: ISO 639-1 language codes

## ❓ Часто задаваемые вопросы

**Q: Как получить coordinates для города?**
A: Можно использовать OpenWeatherMap Geocoding API или другой геокодер. Примеры:
- Москва: 55.7558, 37.6173
- Нью-Йорк: 40.7128, -74.0060
- Лондон: 51.5074, -0.1278
- Токио: 35.6762, 139.6503

**Q: Какой формат единиц по умолчанию?**
A: "metric" (Celsius, м/с)

**Q: Как часто обновляются данные OpenWeatherMap?**
A: Обычно каждые 10-15 минут

**Q: Есть ли ограничения на количество запросов?**
A: Зависит от плана подписки. Свободный план - до 60 запросов в минуту

**Q: Работает ли для координат вне Земли?**
A: Нет, координаты должны быть в диапазоне (-90, 90) для широты и (-180, 180) для долготы

## 🎓 Расширение функционала

Для добавления новых возможностей:

1. **Прогноз на 5 дней**: Используйте `/forecast` endpoint вместо `/weather`
2. **Historical данные**: OpenWeatherMap One Call 3.0 API
3. **Несколько локаций**: Создайте новую интеграцию для batch запросов
4. **Alerts**: Используйте OpenWeatherMap Alerts API

## 📝 История версий

### v1.0.0 (текущая)
- ✅ Получение текущей погоды
- ✅ Поддержка координат (latitude/longitude)
- ✅ Множество языков и единиц измерения
- ✅ Полная обработка ошибок
- ✅ Async/await поддержка
