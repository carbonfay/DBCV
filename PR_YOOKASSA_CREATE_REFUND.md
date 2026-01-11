# Add YooKassa Create Refund Integration

## Описание изменений

Добавлена новая интеграция `YooKassaCreateRefundIntegration` для создания возврата платежа через YooKassa API. Интеграция позволяет создавать полные и частичные возвраты платежей по их ID, включая поддержку различных валют и опциональное описание возврата.

### Основные возможности:
- Создание возврата платежа по ID платежа
- Поддержка полных и частичных возвратов
- Поддержка валют RUB, USD, EUR
- Обработка всех типов ошибок (HTTP статусы, сетевые ошибки)
- Подробное логирование всех операций
- Обратная совместимость с различными форматами credentials

### Технические детали:
- Использует официальную библиотеку `yookassa>=2.3.0` для работы с YooKassa API
- Использует API ключи (shop_id и secret_key) для аутентификации
- Обрабатывает все стандартные HTTP статусы (200, 400, 401, 403, 404, 429, 500)
- Поддерживает graceful degradation при отсутствии библиотеки yookassa
- Возвращает структурированные ответы в формате системы DBCV

### Файлы:
- `backend/app/integrations/yookassa/create_refund.py` - основная реализация интеграции
- `backend/app/integrations/yookassa/__init__.py` - регистрация интеграции
- `backend/app/integrations/__init__.py` - добавлен импорт YooKassa интеграций
- `backend/app/tests/integrations/test_yookassa.py` - комплексные тесты (22 тест-кейса)
- `backend/app/tests/integrations/TEST_CASES_YOOKASSA.md` - документация по тестам

## Тип изменений

<!-- Отметьте галочкой соответствующий пункт -->

- [ ] Исправление бага
- [x] Новая функция
- [ ] Изменение документации
- [ ] Рефакторинг кода
- [x] Тесты
- [ ] Другое (опишите):

## Чеклист

<!-- Отметьте выполненные пункты -->

- [x] Код соответствует стилю проекта
- [x] Я проверил свой код
- [x] Я добавил комментарии к коду, особенно в сложных местах
- [x] Я обновил документацию (если необходимо)
- [x] Мои изменения не генерируют новых предупреждений
- [x] Я добавил тесты, которые подтверждают мои исправления
- [x] Новые и существующие тесты проходят локально

## Как протестировать

### Предварительные требования:

1. **Установить зависимости:**
```bash
cd backend
pip install -r requirements.txt
pip install yookassa>=2.3.0
```

2. **Настроить YooKassa credentials:**
   - Создать магазин в YooKassa (https://yookassa.ru)
   - Получить shop_id (ID магазина) и secret_key (секретный ключ)
   - Добавить credentials в систему через API или UI:
     ```json
     {
       "provider": "yookassa",
       "strategy": "api_key",
       "payload": {
         "shop_id": "YOUR_SHOP_ID",
         "secret_key": "YOUR_SECRET_KEY"
       }
     }
     ```

### Тестирование через API:

1. **Получить каталог интеграций:**
```bash
curl -X GET "http://localhost:8003/api/integrations/catalog?category=payments" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

2. **Получить метаданные интеграции:**
```bash
curl -X GET "http://localhost:8003/api/integrations/yookassa_create_refund/metadata" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

3. **Создать шаг с интеграцией:**
```bash
# Создать connection group с интеграцией
curl -X POST "http://localhost:8003/api/connection_groups/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "step_id": "YOUR_STEP_ID",
    "search_type": "integration",
    "integration_id": "yookassa_create_refund",
    "integration_config": {
      "payment_id": "21740069-000f-50be-b000-0486ffbf45b0",
      "amount": {
        "value": "100.00",
        "currency": "RUB"
      },
      "description": "Возврат по заказу #1234"
    },
    "priority": 0
  }'
```

4. **Выполнить шаг:**
```bash
curl -X POST "http://localhost:8003/api/steps/YOUR_STEP_ID/run" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bot_id": "YOUR_BOT_ID",
    "variables": {},
    "context": {}
  }'
```

### Тестирование через UI:

1. Открыть интерфейс создания шага
2. Добавить новый шаг
3. Добавить Connection Group с типом "integration"
4. Выбрать интеграцию "YooKassa Create Refund"
5. Заполнить параметры:
   - `payment_id`: ID платежа, для которого создается возврат
   - `amount.value`: Сумма возврата (например, "100.00")
   - `amount.currency`: Валюта ("RUB", "USD", или "EUR")
   - `description`: Описание возврата (необязательно)
6. Сохранить и выполнить шаг

### Тестирование различных сценариев:

1. **Успешное создание полного возврата:**
   - Использовать валидный `payment_id` успешного платежа
   - Указать полную сумму возврата
   - Проверить, что возвращается информация о созданном возврате

2. **Успешное создание частичного возврата:**
   - Использовать валидный `payment_id` успешного платежа
   - Указать частичную сумму возврата
   - Проверить, что возвращается информация о созданном возврате

3. **Ошибка 404 (Платеж не найден):**
   - Использовать несуществующий `payment_id`
   - Проверить, что возвращается корректная ошибка 404

4. **Ошибка аутентификации:**
   - Использовать невалидные credentials
   - Проверить, что возвращается ошибка 401

5. **Ошибка 400 (Некорректный запрос):**
   - Попытаться создать возврат на сумму больше суммы платежа
   - Проверить, что возвращается корректная ошибка 400

### Запуск unit тестов:

```bash
# Все тесты YooKassa интеграции
pytest app/tests/integrations/test_yookassa.py -v

# Конкретный тест
pytest app/tests/integrations/test_yookassa.py::test_yookassa_execute_success -v

# С покрытием кода
pytest app/tests/integrations/test_yookassa.py --cov=app.integrations.yookassa --cov-report=html

# Все тесты интеграций
pytest app/tests/integrations/ -v
```

### Ожидаемый результат:

- Интеграция успешно регистрируется в системе
- Метаданные корректно отображаются в каталоге
- Успешные запросы возвращают данные о созданном возврате
- Ошибки обрабатываются корректно с понятными сообщениями
- Все тесты проходят успешно (22 тест-кейса)

## Скриншоты (если применимо)

### Каталог интеграций:
Интеграция должна отображаться в списке интеграций категории "payments" с иконкой YooKassa.

### Метаданные интеграции:
- ID: `yookassa_create_refund`
- Название: "YooKassa Create Refund"
- Категория: "payments"
- Иконка: `icons/integrations/yookassa.svg`
- Цвет: `#FFDB4D`

### Пример конфигурации:
```json
{
  "payment_id": "21740069-000f-50be-b000-0486ffbf45b0",
  "amount": {
    "value": "100.00",
    "currency": "RUB"
  },
  "description": "Возврат по заказу #1234"
}
```

## Дополнительная информация

### Архитектура интеграции:

1. **Базовый класс:** Наследуется от `BaseIntegration`
2. **Метаданные:** Определены через `IntegrationMetadata` с полной схемой конфигурации
3. **Аутентификация:** API ключи через shop_id и secret_key
4. **HTTP клиент:** Использует официальную библиотеку `yookassa` для работы с API
5. **Обработка ошибок:** Полное покрытие всех типов ошибок с логированием

### Особенности реализации:

- **Graceful degradation:** Проверка наличия библиотеки yookassa перед использованием
- **Обратная совместимость:** Поддержка credentials как с `payload`, так и без него
- **Гибкая конфигурация:** Поддержка различных форматов ключей (shop_id/shopId/account_id/accountId)
- **Подробное логирование:** Все операции логируются через BotLogger
- **Обработка исключений:** Корректная обработка всех типов исключений yookassa
- **Поддержка валют:** RUB, USD, EUR

### Безопасность:

- Credentials хранятся в зашифрованном виде через CredentialsResolver
- API ключи используются напрямую через Configuration yookassa
- Используется HTTPS для всех запросов к YooKassa API
- Поддержка тестовых данных для безопасного тестирования

### API YooKassa:

- **API URL:** `https://api.yookassa.ru/v3`
- **Refunds Endpoint:** `POST /v3/refunds`
- **Документация:** https://yookassa.ru/developers/api#create_refund

### Зависимости:

- `yookassa>=2.3.0` - официальная библиотека YooKassa (опционально, проверяется наличие)
- Стандартная библиотека Python (typing, uuid)

### Регистрация:

Интеграция автоматически регистрируется при импорте модуля `app.integrations.yookassa` через:
```python
registry.register(YooKassaCreateRefundIntegration())
```

### Использование в Connection Group:

```python
{
  "search_type": "integration",
  "integration_id": "yookassa_create_refund",
  "integration_config": {
    "payment_id": "{$variable.payment_id$}",  # Поддержка переменных
    "amount": {
      "value": "{$variable.refund_amount$}",
      "currency": "RUB"
    },
    "description": "Возврат по заказу {$variable.order_id$}"
  }
}
```

### Формат ответа:

**Успешный ответ:**
```json
{
  "response": {
    "ok": true,
    "result": {
      "id": "216749f7-0016-50be-b000-078d43a63ae4",
      "status": "succeeded",
      "amount": {
        "value": "100.00",
        "currency": "RUB"
      },
      "created_at": "2017-10-04T19:27:51.407Z",
      "payment_id": "21740069-000f-50be-b000-0486ffbf45b0",
      "description": "Возврат по заказу #1234"
    }
  }
}
```

**Ошибка:**
```json
{
  "response": {
    "ok": false,
    "error_code": 404,
    "description": "Payment not found"
  }
}
```

### Тесты:

Интеграция покрыта **22 тест-кейсами**, включающими:
- Проверку метаданных
- Успешные сценарии (полный и частичный возврат)
- Валидацию входных данных
- Обработку всех типов ошибок API (400, 401, 403, 404, 429, 500)
- Обратную совместимость с credentials
- Обработку опциональных полей

Подробнее см. `backend/app/tests/integrations/TEST_CASES_YOOKASSA.md`

### Связанные файлы:

- `backend/app/integrations/base.py` - базовый класс интеграции
- `backend/app/integrations/registry.py` - реестр интеграций
- `backend/app/engine/integration_handler.py` - обработчик интеграций
- `backend/app/api/routes/integrations.py` - API endpoints для интеграций
- `backend/app/tests/integrations/test_yookassa.py` - тесты интеграции
- `backend/app/tests/integrations/TEST_CASES_YOOKASSA.md` - документация по тестам
