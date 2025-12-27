# Pull Request: Wildberries Get Orders Integration

## Описание

Интеграция для получения списка заказов с пагинацией, фильтрацией по статусу и датам.

## Реализовано

- `WildberriesGetOrdersIntegration` класс с GET методом
- Пагинация (skip/take) с валидацией (1-1000 результатов)
- Фильтрация по статусу заказа
- Фильтрация по диапазону дат
- Полная обработка ошибок
- 15+ unit тестов с полным покрытием
- Техническая документация и примеры

## Чеклист

- [x] Код готов к производству
- [x] Тесты проходят локально
- [x] Документация включена

## Как протестировать

```bash
# Запустить тесты
pytest backend/app/tests/integrations/test_wildberries_get_orders.py -v

# Пример использования
config = {
    "status": "shipped",
    "date_start": "2024-01-01",
    "date_end": "2024-12-31",
    "skip": 0,
    "take": 50
}
result = await integration.execute(config, credentials_resolver, bot_id, logger)
```

## Файлы изменений

| Файл | Описание |
|------|---------|
| `get_orders.py` | Основная реализация (340 строк) |
| `test_wildberries_get_orders.py` | 15+ тестов (400+ строк) |
| `GET_ORDERS.md` | Техническая документация |
| `GET_ORDERS_USAGE.md` | Примеры использования |
