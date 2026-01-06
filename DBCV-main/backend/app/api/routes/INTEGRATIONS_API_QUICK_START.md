# 🚀 Быстрый старт: Тестирование интеграций через API

## Шаг 1: Создайте интеграцию

Создайте файл `backend/app/integrations/{service}/{action}.py` по примеру `telegram/send_message.py`.

## Шаг 2: Зарегистрируйте интеграцию

Добавьте в `backend/app/integrations/{service}/__init__.py`:
```python
from .{action} import {Service}{Action}Integration
from app.integrations.registry import registry

registry.register({Service}{Action}Integration())
```

## Шаг 3: Загрузите иконку в S3

Загрузите SVG иконку в S3 по пути `icons/integrations/{service}.svg`.

## Шаг 4: Протестируйте через API

### 4.1. Получите каталог интеграций

```bash
curl -X GET "http://localhost:8000/api/integrations/catalog" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Ответ:**
```json
{
  "items": [
    {
      "id": "telegram_send_message",
      "name": "Telegram Send Message",
      "icon_url": "https://s3.../icons/integrations/telegram.svg",
      "config_schema": {...}
    }
  ]
}
```

### 4.2. Получите метаданные конкретной интеграции

```bash
curl -X GET "http://localhost:8000/api/integrations/telegram_send_message/metadata" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4.3. Создайте шаг с интеграцией

Используйте существующие endpoints:
- `POST /api/steps/` - создать шаг
- `POST /api/connection_groups/` - создать connection group с `search_type="integration"`

**Пример:**
```bash
# 1. Создайте шаг
curl -X POST "http://localhost:8000/api/steps/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bot_id": "your-bot-id",
    "name": "Telegram Send Message Step",
    "is_proxy": true
  }'

# 2. Создайте connection group с интеграцией
curl -X POST "http://localhost:8000/api/connection_groups/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "step_id": "step-id-from-previous-response",
    "search_type": "integration",
    "integration_id": "telegram_send_message",
    "integration_config": {
      "chat_id": "{$user.telegram_chat_id$}",
      "text": "Hello from DBCV!"
    },
    "connections": [
      {
        "next_step_id": "next-step-id",
        "priority": 0
      }
    ]
  }'
```

## Шаг 5: Протестируйте на фронтенде

1. Откройте Swagger UI: `http://localhost:8000/docs`
2. Найдите endpoints `/api/integrations/*`
3. Протестируйте через Swagger UI

Или используйте Postman/Insomnia для тестирования.

## ✅ Чеклист

- [ ] Интеграция создана и зарегистрирована
- [ ] Иконка загружена в S3
- [ ] API возвращает интеграцию в `/api/integrations/catalog`
- [ ] API возвращает метаданные в `/api/integrations/{id}/metadata`
- [ ] Можно создать шаг с интеграцией через API
- [ ] Интеграция работает при выполнении бота

## 🔍 Отладка

### Интеграция не появляется в каталоге?

1. Проверьте, что интеграция зарегистрирована:
```python
from app.integrations.registry import registry
print(registry.list_all())  # Должна быть ваша интеграция
```

2. Проверьте, что импорт работает:
```python
import app.integrations  # Должен импортировать вашу интеграцию
```

### Иконка не отображается?

1. Проверьте, что иконка загружена в S3:
```python
from app.services.icon_service import icon_service
exists = await icon_service.icon_exists("icons/integrations/your-service.svg")
print(exists)  # Должно быть True
```

2. Проверьте URL иконки:
```python
url = await icon_service.get_icon_url("icons/integrations/your-service.svg")
print(url)  # Должен быть валидный URL
```

## 📚 Дополнительно

- Полная документация API: `backend/app/api/routes/INTEGRATIONS_API.md`
- Пример интеграции: `backend/app/integrations/telegram/send_message.py`
- Документация по созданию интеграций: `backend/app/integrations/README.md`

