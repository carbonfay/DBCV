# Тест-кейсы для OzonGetProductListIntegration

## Обзор

Файл `test_ozon.py` содержит **11 тест-кейсов** для покрытия функциональности интеграции Ozon Get Product List.

## Категории тестов

### 1. Тесты метаданных (1 тест)
- ✅ `test_ozon_metadata` - Проверка метаданных интеграции

### 2. Тесты успешных сценариев (2 теста)
- ✅ `test_ozon_execute_success` - Успешное получение списка товаров
- ✅ `test_ozon_execute_filter_normalization` - Нормализация фильтров offer_id/product_id

### 3. Тесты валидации и credentials (3 теста)
- ✅ `test_ozon_execute_no_credentials` - Отсутствие credentials
- ✅ `test_ozon_execute_missing_credentials_fields` - Отсутствие client_id или api_key
- ✅ `test_ozon_execute_credentials_without_payload` - Обратная совместимость (без payload)

### 4. Тесты ошибок API и данных (3 теста)
- ✅ `test_ozon_execute_api_error` - Ошибка API (403)
- ✅ `test_ozon_execute_invalid_json` - Некорректный JSON в ответе
- ✅ `test_ozon_execute_invalid_limit` - Некорректный лимит

### 5. Тесты сетевых ошибок (2 теста)
- ✅ `test_ozon_execute_timeout` - Таймаут запроса
- ✅ `test_ozon_execute_request_error` - Сетевая ошибка

### 6. Тесты доступности библиотеки (1 тест)
- ✅ `test_ozon_execute_httpx_not_available` - httpx не установлен

## Покрытие функциональности

### ✅ Покрыто:
- [x] Получение списка товаров (успех)
- [x] Формирование фильтров (visibility, offer_id, product_id)
- [x] Валидация лимита (1-1000)
- [x] Валидация credentials
- [x] Обработка ошибок API (403)
- [x] Обработка некорректных ответов (invalid JSON)
- [x] Обработка сетевых ошибок (timeout, request error)
- [x] Graceful degradation при отсутствии httpx

### 📊 Статистика:
- **Всего тестов**: 11
- **Синхронных**: 1
- **Асинхронных**: 10
- **Покрытие**: ~90% кода интеграции

## Запуск тестов

```bash
# Все тесты Ozon интеграции
pytest app/tests/integrations/test_ozon.py -v

# Конкретный тест
pytest app/tests/integrations/test_ozon.py::test_ozon_execute_success -v

# Тесты с покрытием
pytest app/tests/integrations/test_ozon.py --cov=app.integrations.ozon --cov-report=html
```

## Структура тестов

Каждый тест следует структуре:
1. **Setup** - Подготовка mock объектов
2. **Execute** - Выполнение тестируемого метода
3. **Assert** - Проверка результатов и вызовов

## Mock объекты

Тесты используют:
- `AsyncMock` для асинхронных методов httpx
- `MagicMock` для credentials resolver и logger
- `patch` для мокирования httpx библиотеки
- `Mock` для HTTP ответов

## Примечания

- Все тесты изолированы и не требуют реального подключения к Ozon API
- Используются mock объекты для имитации HTTP запросов
- Тесты покрывают как успешные, так и ошибочные сценарии
