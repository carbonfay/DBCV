# Wildberries Get Order Integration

## Описание

Интеграция для получения информации о конкретном заказе из маркетплейса Wildberries через прямые HTTP запросы.

## API Метод

- **Метод**: `GET`
- **Endpoint**: `/api/v1/supplier/orders`
- **URL**: `https://api.wildberries.ru/api/v1/supplier/orders`

## Параметры Конфигурации

### Обязательные параметры

| Параметр | Тип | Описание | Пример |
|----------|-----|---------|---------|
| `order_id` | string | ID заказа в Wildberries (может содержать переменные вроде `{$order.id$}`) | `"12345678"` |

### Опциональные параметры

| Параметр | Тип | Описание | Значение по умолчанию | Примеры |
|----------|-----|---------|--------|---------|
| `detailed` | boolean | Получить детальную информацию о заказе (товары, дополнительные поля) | `false` | `true`, `false` |

## Требования к Credentials

### Provider: `wildberries`
### Strategy: `api_key`

Для работы интеграции необходимо сохранить API ключ (токен) от Wildberries в credentials:

```json
{
  "provider": "wildberries",
  "strategy": "api_key",
  "payload": {
    "api_token": "your_wildberries_api_token_here"
  }
}
```

### Где получить API ключ?

1. Перейти на [openapi.wildberries.ru](https://openapi.wildberries.ru/)
2. Авторизоваться с аккаунтом поставщика
3. Создать API ключ в личном кабинете
4. Скопировать ключ и сохранить в credentials

## Примеры Использования

### Пример 1: Простой запрос информации о заказе

```python
config = {
    "order_id": "12345678",
    "detailed": False
}
```

Результат (успех):
```json
{
  "response": {
    "ok": true,
    "result": {
      "order_id": "12345678",
      "number": "WB001",
      "date": "2024-01-01T00:00:00Z",
      "status": "delivered",
      "total": 1000,
      "currency_code": "RUB"
    }
  }
}
```

### Пример 2: Детальный запрос с полной информацией

```python
config = {
    "order_id": "12345678",
    "detailed": True
}
```

Результат (успех):
```json
{
  "response": {
    "ok": true,
    "result": {
      "order_id": "12345678",
      "number": "WB001",
      "date": "2024-01-01T00:00:00Z",
      "status": "delivered",
      "status_id": 3,
      "status_description": "Доставлено",
      "total": 1000,
      "convertedPrice": 1000,
      "currency_code": "RUB",
      "items": [
        {
          "id": "item_1",
          "name": "Product Name",
          "price": 1000,
          "quantity": 1
        }
      ],
      "address": "Moscow, Russia",
      "supplier_id": "123",
      "client_id": "456",
      "payment_type": "card",
      "comments": "Order comments"
    }
  }
}
```

## Возможные ошибки

### 400 Bad Request
```json
{
  "response": {
    "ok": false,
    "error_code": 400,
    "description": "order_id is required parameter"
  }
}
```

### 401 Unauthorized
```json
{
  "response": {
    "ok": false,
    "error_code": 401,
    "description": "Wildberries API authentication failed"
  }
}
```

**Причины:**
- Неверный API token
- API token истёк
- Сохранённые credentials повреждены

### 404 Not Found
```json
{
  "response": {
    "ok": false,
    "error_code": 404,
    "description": "Order 12345678 not found"
  }
}
```

**Причины:**
- Заказ с таким ID не существует
- Заказ удалён или архивирован
- Неверный ID заказа

### 429 Rate Limit Exceeded
```json
{
  "response": {
    "ok": false,
    "error_code": 429,
    "description": "Rate limit exceeded"
  }
}
```

**Решение:** Подождите перед следующим запросом (Wildberries API имеет ограничения по частоте запросов)

### 500+ Server Error
```json
{
  "response": {
    "ok": false,
    "error_code": 500,
    "description": "Wildberries API server error: 500"
  }
}
```

**Причины:** Проблемы на стороне Wildberries API

### 504 Timeout
```json
{
  "response": {
    "ok": false,
    "error_code": 504,
    "description": "Wildberries API request timeout"
  }
}
```

**Решение:** Повторите запрос позже

## Статусы Заказов

| Статус | ID | Описание |
|--------|-----|---------|
| `pending` | 0 | Заказ ожидает обработки |
| `packed` | 1 | Заказ упакован |
| `shipped` | 2 | Заказ отправлен |
| `delivered` | 3 | Заказ доставлен |
| `cancelled` | 4 | Заказ отменён |
| `returned` | 5 | Заказ возвращён |

## Документация Wildberries API

- **Официальная документация**: https://openapi.wildberries.ru/
- **API для заказов**: https://openapi.wildberries.ru/api/v1/supplier/orders
- **Примеры запросов**: https://openapi.wildberries.ru/docs

## Технические детали реализации

### Используемые библиотеки
- `httpx` - асинхронный HTTP клиент для запросов к API

### Особенности
- Используются прямые HTTP запросы (нет официальной Python библиотеки от Wildberries)
- Поддержка асинхронных операций
- Автоматическая обработка различных кодов ошибок
- Логирование всех операций через BotLogger

### Заголовки запроса
```
Authorization: Bearer {api_token}
Content-Type: application/json
```

## Тестирование

Для тестирования интеграции используйте:

```bash
pytest backend/app/tests/integrations/test_wildberries.py -v
```

### Пример теста

```python
async def test_execute_successful_request():
    integration = WildberriesGetOrderIntegration()
    config = {"order_id": "12345678", "detailed": False}
    
    # ... mock credentials и logger
    
    result = await integration.execute(
        config=config,
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is True
    assert result["response"]["result"]["order_id"] == "12345678"
```

## Limitations and Notes

1. **Rate Limiting**: Wildberries API имеет ограничения по частоте запросов. При получении ошибки 429 (Rate Limit) добавьте задержку перед повторным запросом.

2. **Timeout**: По умолчанию используется timeout 30 секунд. Для получения больших объёмов данных может потребоваться увеличение.

3. **API Version**: Интеграция использует API v1. При выходе новых версий потребуется обновление.

4. **Authentication**: API token хранится в encrypted виде в credentials. Убедитесь, что credentials не будут случайно залогированы.

## История версий

### v1.0.0 (2024-01-01)
- Начальная реализация
- Поддержка получения информации о заказе
- Режимы краткой и детальной информации
- Полная обработка ошибок API
