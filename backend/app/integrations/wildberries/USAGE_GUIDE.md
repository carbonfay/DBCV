# Wildberries Get Order - Руководство по использованию

## 📋 Быстрый старт

### 1. Сохранение API токена

Сначала необходимо сохранить API токен Wildberries в credentials вашего бота:

```bash
POST /api/bots/{bot_id}/credentials

{
  "provider": "wildberries",
  "strategy": "api_key",
  "data": {
    "api_token": "your_wildberries_api_token_here"
  }
}
```

### 2. Использование в шаге бота

При создании шага выберите интеграцию "Wildberries Get Order":

```json
{
  "type": "integration",
  "integration_id": "wildberries_get_order",
  "config": {
    "order_id": "{$user.order_id$}",
    "detailed": true
  }
}
```

### 3. Получение результата

Результат будет доступен в переменной `{$step.result$}`:

```json
{
  "order_id": "12345678",
  "number": "WB001",
  "date": "2024-01-01T00:00:00Z",
  "status": "delivered",
  "status_id": 3,
  "status_description": "Доставлено",
  "total": 1000,
  "currency_code": "RUB",
  "items": [...],
  "address": "Moscow, Russia"
}
```

## 🔧 Конфигурация

### Параметры интеграции

#### order_id (обязательно)
- **Тип**: string
- **Описание**: ID заказа в Wildberries
- **Пример**: `"12345678"` или `"{$user.order_id$}"`

#### detailed (опционально, по умолчанию false)
- **Тип**: boolean
- **Описание**: Получить детальную информацию (товары, статусы и т.д.)
- **Значения**: `true` или `false`

## 📊 Примеры ответов

### Краткая информация (detailed: false)

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

### Детальная информация (detailed: true)

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

## 🚨 Обработка ошибок

### Если заказ не найден (404)

```python
# Обработать в следующем шаге:
if ({$step.result$}.error_code == 404) {
  // Заказ не найден, показать сообщение пользователю
  show_message("Заказ не найден");
}
```

### Если нет доступа к API (401)

```python
// Проверить credentials Wildberries в настройках бота
// Убедиться, что API токен верный
```

### Если превышен лимит запросов (429)

```python
// Подождать и повторить запрос
// Wildberries имеет ограничения по частоте запросов
```

## 💡 Практические примеры

### Пример 1: Получение информации о заказе пользователя

```json
{
  "type": "integration",
  "integration_id": "wildberries_get_order",
  "config": {
    "order_id": "{$user.order_id$}",
    "detailed": false
  }
}
```

**Результат будет в `{$step.result$}` и содержит:**
- order_id
- number
- date
- status
- total
- currency_code

### Пример 2: Проверка статуса заказа

```python
// Предыдущий шаг: Wildberries Get Order
// Текущий шаг: Условие

if ({$step.result$}.status == "delivered") {
  // Заказ доставлен, показать благодарность
} else if ({$step.result$}.status == "cancelled") {
  // Заказ отменён
} else {
  // Заказ в пути
}
```

### Пример 3: Получение информации о товарах

```json
{
  "type": "integration",
  "integration_id": "wildberries_get_order",
  "config": {
    "order_id": "{$user.order_id$}",
    "detailed": true
  }
}
```

**Затем использовать результат:**
```
Ваш заказ содержит товары:
{for item in $step.result$.items}
  - {item.name} ({item.quantity} шт.) - {item.price} ₽
{/for}
```

## 📞 Поддержка

Если возникают проблемы:

1. Проверьте, что API токен Wildberries сохранён в credentials
2. Убедитесь, что order_id передан правильно
3. Посмотрите логи в разделе "Логирование" вашего бота
4. Проверьте статус API Wildberries на их официальном сайте

## 🔗 Полезные ссылки

- [Официальная документация Wildberries API](https://openapi.wildberries.ru/)
- [Получить API токен](https://openapi.wildberries.ru/)
- [Статусы заказов](https://openapi.wildberries.ru/docs)
- [Полная документация интеграции](./GET_ORDER.md)
