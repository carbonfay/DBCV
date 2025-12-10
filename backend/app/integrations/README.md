# Интеграции с внешними сервисами

## Обзор

Система интеграций позволяет использовать готовые библиотеки для работы с внешними сервисами внутри backend кода.

## Структура

```
backend/app/integrations/
    __init__.py              # Автоматическая регистрация
    base.py                  # BaseIntegration, IntegrationMetadata
    registry.py              # IntegrationRegistry
    telegram/
        __init__.py          # Регистрация Telegram интеграций
        send_message.py      # Пример интеграции
```

## Создание новой интеграции

### 1. Создайте файл интеграции

```python
# backend/app/integrations/{service}/{action}.py
from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from uuid import UUID
from typing import Dict, Any

# Импортируйте библиотеку НАПРЯМУЮ в backend код
from {library} import {Class}

class {Service}{Action}Integration(BaseIntegration):
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="{service}_{action}",
            version="1.0.0",
            name="{Service} {Action}",
            description="...",
            category="{category}",  # messaging, ai, storage, weather, maps, payments, crm, ecommerce, education, medicine, news, translation
            icon_s3_key="icons/integrations/{service}.svg",
            color="#...",
            config_schema={...},
            credentials_provider="{service}",
            credentials_strategy="api_key",  # или "oauth"
            library_name="{library}"
        )
    
    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger
    ) -> Dict[str, Any]:
        # Получаем credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="{service}",
            strategy="api_key"
        )
        
        if not creds:
            return {"response": {"ok": False, "error_code": 401, "description": "Credentials not found"}}
        
        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        client = {Class}(token=creds["token"])
        result = await client.{method}(...)
        
        # Возвращаем в формате системы
        return {"response": {"ok": True, "result": {...}}}
```

### 2. Зарегистрируйте интеграцию

```python
# backend/app/integrations/{service}/__init__.py
from .{action} import {Service}{Action}Integration
from app.integrations.registry import registry

registry.register({Service}{Action}Integration())
```

### 3. Добавьте импорт в главный __init__.py

```python
# backend/app/integrations/__init__.py
try:
    from app.integrations.{service} import *  # noqa: F401, F403
except ImportError:
    pass
```

## Пример: Telegram Send Message

См. `backend/app/integrations/telegram/send_message.py` - полный рабочий пример.

**Библиотека**: `python-telegram-bot>=20.0` (официально рекомендованная, безопасная)

## Безопасные библиотеки

См. `backend/app/integrations/SAFE_LIBRARIES.md` - полный список безопасных библиотек для всех категорий интеграций.

**Важно**: Используйте только проверенные, официальные библиотеки или прямые HTTP запросы через `httpx`.

## Категории интеграций

- `messaging` - Мессенджеры (Telegram, Discord, VK)
- `ai` - AI сервисы (OpenAI, YandexGPT)
- `storage` - Хранилища (Google Drive, Dropbox)
- `weather` - Погода (OpenWeatherMap, Яндекс.Погода)
- `maps` - Карты (Яндекс.Карты, Google Maps)
- `payments` - Платежи (ЮKassa, Stripe, PayPal)
- `crm` - CRM системы (Битрикс24, AmoCRM, HubSpot)
- `ecommerce` - E-commerce (Wildberries, Ozon)
- `education` - Образование (Moodle, Google Classroom)
- `medicine` - Медицина (Медицинские справочники)
- `news` - Новости (NewsAPI, Яндекс.Новости)
- `translation` - Переводы (Яндекс.Переводчик, Google Translate)

## Использование в Connection Group

Создайте Connection Group с:
- `search_type="integration"`
- `integration_id="telegram_send_message"`
- `integration_config={"chat_id": "...", "text": "..."}`

## Тестирование

См. примеры тестов в `backend/app/tests/integrations/`.

## Пример: Yandex Weather Get Forecast

Пример использования интеграции `yandex_weather_get_forecast`.

- Integration ID: `yandex_weather_get_forecast`
- Credentials provider: `yandex_weather` (strategy: `api_key`)

Пример конфигурации (дневной прогноз по координатам):

```json
{
    "latitude": 55.75,
    "longitude": 37.62,
    "lang": "ru_RU",
    "extra": false,
    "hours": false,
    "limit": 3
}
```

Пример конфигурации (почасовой прогноз с дополнительными данными):

```json
{
    "latitude": 59.93,
    "longitude": 30.33,
    "lang": "ru_RU",
    "extra": true,
    "hours": true,
    "limit": 2
}
```

Пример ожидаемого результата (успех):

```json
{
    "response": {
        "ok": true,
        "result": {
            "now": 1600000000,
            "now_dt": "2020-09-13T12:00:00Z",
            "forecasts": [ ... ],
            "info": {"lat": 55.75, "lon": 37.62 }
        }
    }
}
```

Если API ключ недоступен, интеграция вернёт:

```json
{ "response": { "ok": false, "error_code": 401, "description": "Yandex Weather API key not found in credentials" } }
```

Добавлены тесты: `backend/app/tests/integrations/test_yandex_weather.py` (мок httpx).

