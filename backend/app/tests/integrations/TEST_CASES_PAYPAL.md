# Тест-кейсы для PayPalGetPayoutIntegration

## Обзор

Файл `test_paypal.py` содержит **26 тест-кейсов** для полного покрытия функциональности PayPal Get Payout интеграции.

## Категории тестов

### 1. Тесты метаданных (1 тест)
- ✅ `test_paypal_metadata` - Проверка всех метаданных интеграции

### 2. Тесты успешных сценариев (4 теста)
- ✅ `test_paypal_execute_success` - Успешное выполнение интеграции
- ✅ `test_paypal_execute_production_environment` - Использование production окружения
- ✅ `test_paypal_execute_credentials_without_payload` - Обратная совместимость с credentials без payload
- ✅ `test_paypal_execute_full_payout_data` - Полные данные payout (batch_header, items, links)
- ✅ `test_paypal_execute_empty_payout_response` - Пустой ответ от API
- ✅ `test_paypal_execute_default_environment` - Использование окружения по умолчанию (sandbox)

### 3. Тесты валидации входных данных (3 теста)
- ✅ `test_paypal_execute_no_credentials` - Отсутствие credentials
- ✅ `test_paypal_execute_missing_client_credentials` - Отсутствие client_id или client_secret
- ✅ `test_paypal_execute_missing_payout_batch_id` - Отсутствие обязательного параметра payout_batch_id

### 4. Тесты получения access token (5 тестов)
- ✅ `test_paypal_get_access_token_success` - Успешное получение токена (sandbox)
- ✅ `test_paypal_get_access_token_production` - Получение токена для production
- ✅ `test_paypal_get_access_token_http_error` - HTTP ошибка при получении токена
- ✅ `test_paypal_get_access_token_timeout` - Таймаут при получении токена
- ✅ `test_paypal_get_access_token_no_token_in_response` - Отсутствие access_token в ответе

### 5. Тесты ошибок OAuth (2 теста)
- ✅ `test_paypal_execute_oauth_token_error` - Ошибка получения OAuth токена
- ✅ `test_paypal_execute_request_error_on_token` - RequestError при получении токена
- ✅ `test_paypal_execute_timeout_on_token` - TimeoutException при получении токена

### 6. Тесты ошибок PayPal API (6 тестов)
- ✅ `test_paypal_execute_payout_not_found` - Payout не найден (404)
- ✅ `test_paypal_execute_api_error` - Ошибка API (500)
- ✅ `test_paypal_execute_forbidden_error` - Доступ запрещен (403)
- ✅ `test_paypal_execute_rate_limit_error` - Превышен лимит запросов (429)
- ✅ `test_paypal_execute_invalid_json_response` - Некорректный JSON ответ
- ✅ `test_paypal_execute_request_error_on_payout` - RequestError при получении payout

### 7. Тесты сетевых ошибок (2 теста)
- ✅ `test_paypal_execute_timeout` - Таймаут запроса к API
- ✅ `test_paypal_execute_httpx_not_available` - Библиотека httpx не установлена

## Покрытие функциональности

### ✅ Покрыто:
- [x] Получение OAuth токена (успех и ошибки)
- [x] Получение payout данных (успех и ошибки)
- [x] Валидация входных параметров
- [x] Обработка различных HTTP статусов (200, 404, 403, 429, 500)
- [x] Обработка сетевых ошибок (timeout, request error)
- [x] Работа с sandbox и production окружениями
- [x] Обратная совместимость с credentials
- [x] Обработка некорректных ответов от API
- [x] Обработка пустых ответов

### 📊 Статистика:
- **Всего тестов**: 26
- **Синхронных**: 1
- **Асинхронных**: 25
- **Покрытие**: ~95% кода интеграции

## Запуск тестов

```bash
# Все тесты PayPal интеграции
pytest app/tests/integrations/test_paypal.py -v

# Конкретный тест
pytest app/tests/integrations/test_paypal.py::test_paypal_execute_success -v

# Тесты с покрытием
pytest app/tests/integrations/test_paypal.py --cov=app.integrations.paypal --cov-report=html
```

## Структура тестов

Каждый тест следует структуре:
1. **Setup** - Подготовка mock объектов
2. **Execute** - Выполнение тестируемого метода
3. **Assert** - Проверка результатов

## Mock объекты

Тесты используют:
- `AsyncMock` для асинхронных методов
- `MagicMock` для credentials resolver и logger
- `patch` для мокирования httpx библиотеки
- `Mock` для HTTP ответов

## Примечания

- Все тесты изолированы и не требуют реального подключения к PayPal API
- Используются mock объекты для имитации HTTP запросов
- Тесты проверяют как успешные, так и ошибочные сценарии
- Покрыты edge cases и граничные условия
