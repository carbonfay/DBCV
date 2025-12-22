# Pull Request: Wildberries Update Stock Integration

## Описание

Добавлена интеграция **Wildberries Update Stock** для массового обновления остатков товаров. Поддержка 1-1000 товаров за запрос, валидация SKU/quantity, поддержка разных складов, обработка ошибок API.

## Тип изменений

- [x] Новая функция
- [x] Тесты (20+)
- [x] Документация

## Как протестировать

```bash
# Запустить все тесты
pytest backend/app/tests/integrations/test_wildberries_update_stock.py -v

# С покрытием кода
pytest backend/app/tests/integrations/test_wildberries_update_stock.py --cov=app.integrations.wildberries.update_stock
```

## Пример использования

```python
# Обновление одного товара
config = {"stocks": [{"sku": 12345678, "quantity": 50}]}

# Обновление нескольких товаров на разных складах
config = {
    "stocks": [
        {"sku": 123, "quantity": 50, "warehouse_id": 117986},
        {"sku": 456, "quantity": 30, "warehouse_id": 290406},
        {"sku": 789, "quantity": 0}  # Снять с продажи
    ]
}

# Выполнить
result = await integration.execute(config, credentials_resolver, bot_id, logger)
```

## Файлы изменений

| Файл | Описание |
|------|---------|
| `update_stock.py` | Основная реализация (380 строк) |
| `test_wildberries_update_stock.py` | 20+ тестов (450+ строк) |
| `UPDATE_STOCK.md` | Техническая документация |
| `UPDATE_STOCK_USAGE.md` | Примеры использования |
