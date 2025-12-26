# Wildberries Интеграции

## Обзор
Модуль интеграций с платформой Wildberries для управления товарами и остатками.

## Доступные интеграции

### 1. WildberriesUpdateStockIntegration
**ID:** `wildberries_update_stock`  
**Версия:** `1.0.0`  
**Категория:** `ecommerce`

Обновляет количество товара (остатки) по артикулу на платформе Wildberries.

#### Требования
- Установленная библиотека: `wildberries-api>=1.2.0`
- Credentials: API ключ Wildberries (provider: `wildberries`, strategy: `api_key`)

#### Параметры конфигурации

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `sku` | string | Да | Артикул товара на Wildberries |
| `stock` | integer | Да | Количество на складе (≥0) |
| `warehouse_id` | string | Нет | ID склада (опционально) |

#### Пример использования

```json
{
  "integration_id": "wildberries_update_stock",
  "config": {
    "sku": "WB12345",
    "stock": 50,
    "warehouse_id": "optional_warehouse_id"
  }
}
```

#### Формат ответа

```json
{
  "response": {
    "ok": true,
    "error_code": null,
    "description": null,
    "error": null,
    "result": {
      // Результат от Wildberries API
    }
  }
}
```

#### Коды ошибок

| Код | Описание |
|-----|----------|
| 400 | Неверные параметры (отсутствует sku/stock или stock < 0) |
| 401 | Ошибка аутентификации (неверный API ключ) |
| 500 | Библиотека wildberries_api не установлена |
| 502 | Пустой ответ от API Wildberries |
| 504 | Таймаут запроса (>30 секунд) |

## Установка

### 1. Установите зависимости
```bash
pip install wildberries-api>=1.2.0
```

### 2. Настройка credentials
Добавьте API ключ Wildberries через систему credentials:
- Provider: `wildberries`
- Strategy: `api_key`
- Payload: `{"api_key": "your_wildberries_api_key"}`

## Регистрация
Интеграция автоматически регистрируется при импорте модуля `app.integrations.Wildberries`.

## Логирование
Все операции логируются через `BotLogger` с различными уровнями:
- `INFO`: Начало/завершение операции
- `DEBUG`: Детали запросов и параметры
- `WARNING`: Повторные попытки
- `ERROR`: Ошибки валидации и API
- `CRITICAL`: Неожиданные исключения

## Примечания
- Библиотека является опциональной зависимостью
- При отсутствии библиотеки интеграция вернет ошибку 500
- Таймаут API запросов: 30 секунд
- Поддерживается retry при TypeError (попытка без warehouse_id)
</contents>