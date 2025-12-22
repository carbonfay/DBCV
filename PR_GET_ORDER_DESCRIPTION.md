# Pull Request: Wildberries Get Order Integration

## Описание

Интеграция для получения информации о конкретном заказе из Wildberries.

## Реализовано

- `WildberriesGetOrderIntegration` класс с GET методом
- Два режима: краткая и детальная информация
- Полная обработка ошибок (400, 401, 404, 429, 500+, timeout)
- 9+ unit тестов с полным покрытием
- Техническая документация и примеры

## Чеклист

- [x] Код готов к производству
- [x] Тесты проходят локально
- [x] Документация включена

## Как протестировать

```bash
# Запустить тесты
pytest backend/app/tests/integrations/test_wildberries.py -v

# Пример использования
config = {
    "order_id": "12345678",
    "detailed": True
}
result = await integration.execute(config, credentials_resolver, bot_id, logger)
```

## Файлы изменений

| Файл | Описание |
|------|---------|
| `get_order.py` | Основная реализация (309 строк) |
| `test_wildberries.py` | 9+ тестов (350+ строк) |
| `GET_ORDER.md` | Техническая документация |
| `USAGE_GUIDE.md` | Примеры использования |
