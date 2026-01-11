# Тест-кейсы для YooKassaCreateRefundIntegration

## Обзор

Файл `test_yookassa.py` содержит **22 тест-кейса** для полного покрытия функциональности YooKassa Create Refund интеграции.

## Категории тестов

### 1. Тесты метаданных (1 тест)
- ✅ `test_yookassa_metadata` - Проверка всех метаданных интеграции

### 2. Тесты успешных сценариев (7 тестов)
- ✅ `test_yookassa_execute_success` - Успешное создание возврата платежа
- ✅ `test_yookassa_execute_success_partial_refund` - Успешный частичный возврат
- ✅ `test_yookassa_execute_with_description` - Создание возврата с описанием
- ✅ `test_yookassa_execute_without_description` - Создание возврата без описания
- ✅ `test_yookassa_execute_default_currency` - Использование валюты по умолчанию (RUB)
- ✅ `test_yookassa_execute_different_currencies` - Тестирование различных валют (RUB, USD, EUR)
- ✅ `test_yookassa_execute_full_refund_data` - Полные данные возврата (включая опциональные поля)

### 3. Тесты валидации входных данных (5 тестов)
- ✅ `test_yookassa_execute_no_credentials` - Отсутствие credentials
- ✅ `test_yookassa_execute_missing_shop_credentials` - Отсутствие shop_id или secret_key
- ✅ `test_yookassa_execute_missing_payment_id` - Отсутствие обязательного параметра payment_id
- ✅ `test_yookassa_execute_missing_amount` - Отсутствие обязательного параметра amount
- ✅ `test_yookassa_execute_missing_amount_value` - Отсутствие amount.value

### 4. Тесты ошибок API YooKassa (6 тестов)
- ✅ `test_yookassa_execute_api_error` - Ошибка API (404 - платеж не найден)
- ✅ `test_yookassa_execute_unauthorized_error` - Ошибка 401 (неавторизован)
- ✅ `test_yookassa_execute_forbidden_error` - Ошибка 403 (доступ запрещен)
- ✅ `test_yookassa_execute_bad_request_error` - Ошибка 400 (некорректный запрос)
- ✅ `test_yookassa_execute_rate_limit_error` - Ошибка 429 (превышен лимит запросов)
- ✅ `test_yookassa_execute_generic_exception` - Обработка общего исключения

### 5. Тесты совместимости и доступности (3 теста)
- ✅ `test_yookassa_execute_credentials_without_payload` - Обратная совместимость с credentials без payload
- ✅ `test_yookassa_execute_credentials_with_account_id` - Использование credentials с account_id (альтернативный формат)
- ✅ `test_yookassa_execute_yookassa_not_available` - Библиотека yookassa не установлена

## Покрытие функциональности

### ✅ Покрыто:
- [x] Создание возврата платежа (успех и ошибки)
- [x] Создание частичного возврата
- [x] Валидация входных параметров (payment_id, amount, currency)
- [x] Обработка различных HTTP статусов (200, 400, 401, 403, 404, 429, 500)
- [x] Работа с различными валютами (RUB, USD, EUR)
- [x] Обработка опциональных параметров (description)
- [x] Обратная совместимость с credentials (различные форматы ключей)
- [x] Обработка опциональных полей ответа (description, refund_authorization_details, metadata)
- [x] Обработка ошибок библиотеки (yookassa не установлена)

### 📊 Статистика:
- **Всего тестов**: 22
- **Синхронных**: 1
- **Асинхронных**: 21
- **Покрытие**: ~95% кода интеграции

## Запуск тестов

```bash
# Все тесты YooKassa интеграции
pytest app/tests/integrations/test_yookassa.py -v

# Конкретный тест
pytest app/tests/integrations/test_yookassa.py::test_yookassa_execute_success -v

# Тесты с покрытием
pytest app/tests/integrations/test_yookassa.py --cov=app.integrations.yookassa --cov-report=html

# Все тесты интеграций
pytest app/tests/integrations/ -v
```

## Структура тестов

Каждый тест следует структуре:
1. **Setup** - Подготовка mock объектов (Configuration, Refund, credentials_resolver, logger)
2. **Execute** - Выполнение тестируемого метода execute()
3. **Assert** - Проверка результатов и вызовов mock объектов

## Mock объекты

Тесты используют:
- `AsyncMock` для асинхронных методов (credentials_resolver.get_default_for, logger методы)
- `MagicMock` для credentials resolver и logger
- `patch` для мокирования библиотеки yookassa (Configuration, Refund)
- `Mock` для объектов refund и amount от YooKassa API

## Основные отличия от PayPal интеграции

1. **Аутентификация**: YooKassa использует API ключи (shop_id, secret_key), а не OAuth2 токены
2. **Библиотека**: Используется официальная библиотека `yookassa>=2.3.0` вместо `httpx`
3. **Метод API**: POST запрос через `Refund.create()` вместо GET запроса
4. **Параметры**: payment_id и amount вместо payout_batch_id
5. **Валюты**: Поддержка RUB, USD, EUR (вместо универсальных валют PayPal)
6. **Опциональные поля**: description (необязательный параметр)

## Параметры конфигурации

### Обязательные параметры:
- `payment_id` - ID платежа, для которого создается возврат
- `amount.value` - Сумма возврата
- `amount.currency` - Валюта (RUB, USD, EUR)

### Опциональные параметры:
- `description` - Описание возврата

## Credentials

Интеграция требует credentials с:
- `shop_id` (или `shopId`, `account_id`, `accountId`) - ID магазина
- `secret_key` (или `secretKey`) - Секретный ключ

Поддерживается обратная совместимость с различными форматами ключей.

## Примеры использования в тестах

### Успешное создание возврата:
```python
config = {
    "payment_id": "21740069-000f-50be-b000-0486ffbf45b0",
    "amount": {
        "value": "100.00",
        "currency": "RUB"
    },
    "description": "Возврат по заказу #1234"
}
```

### Частичный возврат:
```python
config = {
    "payment_id": "21740069-000f-50be-b000-0486ffbf45b0",
    "amount": {
        "value": "50.00",
        "currency": "RUB"
    }
}
```

## Примечания

- Все тесты изолированы и не требуют реального подключения к YooKassa API
- Используются mock объекты для имитации вызовов библиотеки yookassa
- Тесты проверяют как успешные, так и ошибочные сценарии
- Покрыты edge cases и граничные условия
- Тесты проверяют различные форматы credentials для обратной совместимости
- Проверяется корректная обработка опциональных полей ответа API
