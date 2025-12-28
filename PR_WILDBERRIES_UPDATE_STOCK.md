# PR: Wildberries Update Stock Integration

## Описание
Реализована интеграция Wildberries Update Stock для обновления остатков товаров на маркетплейсе Wildberries.

## Изменения
- Добавлен файл `backend/app/integrations/wildberries/update_stock.py`
- Зарегистрирована интеграция в `backend/app/integrations/wildberries/__init__.py`
- Использована библиотека `httpx` для прямых HTTP запросов к Wildberries API

## Функциональность
- Обновление остатков товаров по баркоду
- Поддержка массового обновления (несколько товаров за один запрос)
- Опциональное указание ID склада
- Валидация входных данных (баркод, количество)
- Обработка всех типов ошибок API (400, 401, 403, 429, 504)

## API Endpoint
```
PUT https://marketplace-api.wildberries.ru/api/v2/supplier/stocks
```

## Тестирование
- [x] Проверен синтаксис Python
- [x] Интеграция успешно импортируется и создается
- [x] Метаданные корректно возвращаются
- [x] Коммит создан и отправлен в репозиторий
- [ ] Протестирована через API (`/api/v1/integrations/catalog`)
- [ ] Протестирована в боте (создан Connection Group, выполнена интеграция)
- [ ] Проверена визуально на фронте
- [ ] Проверена с реальным API ключом Wildberries

## Результаты тестирования
```
============================================================
Wildberries Update Stock Integration
============================================================
ID: wildberries_update_stock
Version: 1.0.0
Name: Wildberries Update Stock
Description: Обновление остатков товаров в Wildberries
Category: ecommerce
Credentials Provider: wildberries
Library: httpx (прямые HTTP запросы)
Examples count: 2
============================================================
✅ Integration registered successfully!
============================================================
```

## Примеры использования

### 1. Обновить остатки для одного товара
```json
{
  "stocks": [
    {
      "barcode": "1234567890123",
      "stock": 10,
      "warehouse_id": 123
    }
  ]
}
```

### 2. Обновить остатки для нескольких товаров
```json
{
  "stocks": [
    {
      "barcode": "1234567890123",
      "stock": 5
    },
    {
      "barcode": "9876543210987",
      "stock": 15,
      "warehouse_id": 123
    }
  ]
}
```

### 3. Обновить остатки без указания склада
```json
{
  "stocks": [
    {
      "barcode": "1234567890123",
      "stock": 20
    }
  ]
}
```

## Формат ответа

### Успешный ответ
```json
{
  "response": {
    "ok": true,
    "result": {
      "updated": 2,
      "details": {
        "success": true,
        "stocks": [...]
      }
    }
  }
}
```

### Ошибка
```json
{
  "response": {
    "ok": false,
    "error_code": 400,
    "description": "Bad request: Invalid barcode format"
  }
}
```

## Обработка ошибок
- **400 Bad Request**: Неверный формат данных или баркода
- **401 Unauthorized**: Неверный API ключ
- **403 Forbidden**: API ключ не имеет прав на обновление остатков
- **429 Too Many Requests**: Превышен лимит запросов
- **504 Gateway Timeout**: Таймаут запроса к API
- **500 Internal Server Error**: Непредвиденная ошибка

## Валидация данных
- ✅ Проверка наличия обязательных полей (barcode, stock)
- ✅ Проверка типа данных (stock должен быть целым числом)
- ✅ Проверка диапазона значений (stock >= 0)
- ✅ Проверка наличия хотя бы одного товара в массиве stocks

## Чеклист
- [x] Код следует стилю проекта
- [x] Используется правильная библиотека (`httpx` для HTTP запросов)
- [x] Credentials получаются через CredentialsResolver
- [x] Обработка ошибок реализована (все типы HTTP ошибок)
- [x] Метаданные заполнены полностью (id, name, description, category, icon_s3_key, config_schema)
- [x] Добавлены примеры использования в examples (2 примера)
- [x] Версия указана корректно ("1.0.0")
- [x] Валидация входных данных реализована
- [x] Поддержка массового обновления (batch update)

## Требования к credentials
```json
{
  "provider": "wildberries",
  "strategy": "api_key",
  "payload": {
    "api_key": "YOUR_WILDBERRIES_API_KEY"
  }
}
```

## API документация
- Wildberries Marketplace API: https://openapi.wildberries.ru/
- Endpoint документация: https://openapi.wildberries.ru/#tag/Marketplace-Ostatki

## Безопасность
- ✅ API ключ передается через заголовки (X-API-KEY и Authorization)
- ✅ Использование HTTPS для всех запросов
- ✅ Валидация входных данных перед отправкой
- ✅ Логирование ошибок без раскрытия API ключа

## Производительность
- Поддержка batch операций (до нескольких товаров в одном запросе)
- Таймаут запроса: 30 секунд
- Асинхронные HTTP запросы через httpx.AsyncClient

## История коммитов
```
3db70d8 - Рефакторинг: переименование папки Vildberries в wildberries
6e4ba39 - Rename Wildberries to Vildberries and clean up integration files
757f8da - Merge branch 'feature/wildberries-update-stock'
ac6f15f - Remove Wildberries README.md documentation file
a93f049 - Add Wildberries integration with update_stock functionality
```

## Видео
[Ссылка на видео с демонстрацией будет добавлена]

---

**Автор**: Chuprakov Ivan Petrovich  
**Дата**: 2025-12-28  
**Ветка**: `integration/Wildberries_Update_Stock/Chuprakov_Ivan_Petrovich`