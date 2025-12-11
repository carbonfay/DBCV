# OpenWeatherMap Integration

## Описание

Интеграция для получения индекса ультрафиолета (UV Index) из OpenWeatherMap API.

**ID интеграции:** `openweathermap_get_uv_index`
**Версия:** `1.0.0`
**Категория:** Weather

## Необходимые ключи

### OpenWeatherMap API Key

Требуется API ключ от OpenWeatherMap для работы интеграции. Получить ключ можно:

1. Перейти на https://openweathermap.org/api
2. Зарегистрироваться или войти в свой аккаунт
3. Перейти в раздел "API keys"
4. Скопировать API ключ

### Требования к API ключу

- API ключ должен иметь доступ к "One Call API 2.0" или "UV Index API"
- Обычно включено в бесплатном плане

## Конфигурация

### Параметры

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| `latitude` | number | Да | Широта (-90 до 90) |
| `longitude` | number | Да | Долгота (-180 до 180) |

### Примеры конфигурации

#### Получить UV Index для Москвы
```json
{
  "latitude": 55.7558,
  "longitude": 37.6173
}
```

#### Получить UV Index для Санкт-Петербурга
```json
{
  "latitude": 59.9311,
  "longitude": 30.3609
}
```

## Результат

### Успешный ответ

```json
{
  "response": {
    "ok": true,
    "result": {
      "uv_index": 7.5,
      "latitude": 55.7558,
      "longitude": 37.6173,
      "date": "2025-12-09",
      "date_iso": "2025-12-09T12:00:00Z"
    }
  }
}
```

### Ошибка

```json
{
  "response": {
    "ok": false,
    "error": "Описание ошибки"
  }
}
```

## Шкала UV Index

- **0-2**: Низкий риск
- **3-5**: Средний риск
- **6-7**: Высокий риск
- **8-10**: Очень высокий риск
- **11+**: Экстремальный риск

## Возможные ошибки

| Ошибка | Описание |
|--------|----------|
| `Latitude и longitude являются обязательными параметрами` | Отсутствует один или оба параметра |
| `Latitude должна быть в диапазоне от -90 до 90` | Значение широты некорректно |
| `Longitude должна быть в диапазоне от -180 до 180` | Значение долготы некорректно |
| `API ключ OpenWeatherMap не найден` | Не настроены credentials |
| `OpenWeatherMap API вернула ошибку [статус]` | Ошибка при запросе к API |
| `Timeout при запросе к OpenWeatherMap API` | Запрос выполнялся слишком долго |

## Тестирование

Для запуска тестов:

```bash
pytest app/tests/integrations/test_openweathermap.py -v
```

## Примеры использования

### Получить UV Index в боте

```python
from app.integrations.registry import registry

# Получить интеграцию
integration = registry.get("openweathermap_get_uv_index")

# Выполнить интеграцию
result = await integration.execute(
    config={
        "latitude": 55.7558,
        "longitude": 37.6173
    },
    credentials_resolver=credentials_resolver,
    bot_id=bot_id,
    logger=logger
)

# Получить результат
if result["response"]["ok"]:
    uv_index = result["response"]["result"]["uv_index"]
    print(f"UV Index: {uv_index}")
else:
    print(f"Ошибка: {result['response']['error']}")
```

## Примечания

- OpenWeatherMap API имеет rate limit. Бесплатный план ограничен 60 запросами в минуту
- Данные обновляются каждый час
- Широта и долгота должны быть в формате десятичных дробей (например, 55.7558, а не 55°45'20.9")
