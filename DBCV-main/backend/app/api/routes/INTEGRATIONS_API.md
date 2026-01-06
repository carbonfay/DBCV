# API Endpoints для интеграций

## Интеграции (Integrations)

### GET /api/integrations/catalog

Получить каталог всех доступных интеграций.

**Query параметры:**
- `category` (optional): Фильтр по категории (messaging, ai, storage, weather, maps, payments, crm, ecommerce, education, medicine, news, translation)
- `latest_only` (optional, default: true): Возвращать только последние версии

**Пример запроса:**
```bash
GET /api/integrations/catalog?category=messaging&latest_only=true
```

**Пример ответа:**
```json
{
  "items": [
    {
      "id": "telegram_send_message",
      "version": "1.0.0",
      "name": "Telegram Send Message",
      "description": "Отправка текстового сообщения в Telegram через Bot API",
      "category": "messaging",
      "icon_url": "https://s3.../icons/integrations/telegram.svg?signature=...",
      "color": "#0088cc",
      "config_schema": {
        "type": "object",
        "required": ["chat_id", "text"],
        "properties": {
          "chat_id": {"type": "string"},
          "text": {"type": "string"},
          "parse_mode": {"type": "string", "enum": ["HTML", "Markdown", "MarkdownV2"]}
        }
      },
      "credentials_provider": "telegram",
      "credentials_strategy": "api_key",
      "library_name": "python-telegram-bot>=20.0",
      "examples": [
        {
          "title": "Простое сообщение",
          "config": {
            "chat_id": "{$user.telegram_chat_id$}",
            "text": "Hello from DBCV!"
          }
        }
      ]
    }
  ]
}
```

### GET /api/integrations/{integration_id}/metadata

Получить метаданные конкретной интеграции.

**Path параметры:**
- `integration_id`: ID интеграции (например, "telegram_send_message")

**Query параметры:**
- `version` (optional): Версия интеграции (если не указана, возвращается последняя)

**Пример запроса:**
```bash
GET /api/integrations/telegram_send_message/metadata
```

**Пример ответа:**
```json
{
  "id": "telegram_send_message",
  "version": "1.0.0",
  "name": "Telegram Send Message",
  "description": "Отправка текстового сообщения в Telegram через Bot API",
  "category": "messaging",
  "icon_url": "https://s3.../icons/integrations/telegram.svg?signature=...",
  "color": "#0088cc",
  "config_schema": {...},
  "credentials_provider": "telegram",
  "credentials_strategy": "api_key",
  "library_name": "python-telegram-bot>=20.0",
  "examples": [...]
}
```

## Presets (Заготовки шагов)

### GET /api/presets/catalog

Получить каталог всех доступных presets.

**Query параметры:**
- `category` (optional): Фильтр по категории (logic, flow, integration)

**Пример запроса:**
```bash
GET /api/presets/catalog?category=logic
```

**Пример ответа:**
```json
{
  "items": [
    {
      "id": "conditional",
      "name": "Conditional Step (IF/ELSE)",
      "description": "Шаг с условным переходом",
      "category": "logic",
      "icon_url": "https://s3.../icons/presets/conditional.svg?signature=...",
      "color": "#FF9800",
      "config_schema": {...},
      "examples": [...]
    }
  ]
}
```

**Примечание:** Presets пока не реализованы, endpoint возвращает пустой список.

### POST /api/presets/create-step

Создать шаг используя preset.

**Body:**
```json
{
  "preset_id": "conditional",
  "bot_id": "uuid",
  "config": {
    "condition": {...},
    "if_step_id": "uuid",
    "else_step_id": "uuid"
  },
  "name": "Optional step name",
  "pos_x": 100,
  "pos_y": 200
}
```

**Пример ответа:**
```json
{
  "step": {
    "id": "uuid",
    "name": "Conditional Step",
    "bot_id": "uuid",
    ...
  },
  "connection_group": {
    "id": "uuid",
    "search_type": "message",
    "connections": [...]
  }
}
```

**Примечание:** Presets пока не реализованы, endpoint возвращает 501.

## Иконки (Icons)

### GET /api/icons/{s3_key}

Получить URL иконки из S3 (редирект на presigned URL).

**Path параметры:**
- `s3_key`: S3 ключ иконки (например, "icons/integrations/telegram.svg")

**Пример запроса:**
```bash
GET /api/icons/icons/integrations/telegram.svg
```

**Ответ:** Редирект (302) на presigned URL из S3

## Аутентификация

Все endpoints требуют аутентификации через `CurrentUser` dependency.

## Использование на фронтенде

### Пример: Получить каталог интеграций

```javascript
const response = await fetch('/api/integrations/catalog?category=messaging', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
const data = await response.json();
console.log(data.items); // Список интеграций
```

### Пример: Получить метаданные интеграции

```javascript
const response = await fetch('/api/integrations/telegram_send_message/metadata', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
const metadata = await response.json();
console.log(metadata.config_schema); // Схема для формы
```

### Пример: Использовать иконку

```html
<img src="/api/icons/icons/integrations/telegram.svg" alt="Telegram" />
```

Или напрямую использовать `icon_url` из ответа catalog/metadata.

