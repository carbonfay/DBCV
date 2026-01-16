# Add Ozon Get Product List Integration

## Описание изменений

Добавлена новая интеграция `OzonGetProductListIntegration` для получения списка товаров через Ozon Seller API. Интеграция поддерживает фильтрацию по видимости, offer_id и product_id, а также пагинацию через last_id.

### Основные возможности:
- Получение списка товаров через `POST /v2/product/list`
- Фильтрация по visibility, offer_id, product_id
- Пагинация через last_id
- Обработка ошибок API и сетевых ошибок
- Обратная совместимость с различными форматами credentials

### Технические детали:
- Использует `httpx` для прямых HTTP запросов к Ozon API
- Аутентификация через `Client-Id` и `Api-Key`
- Обрабатывает стандартные HTTP статусы (200, 400, 401, 403, 404, 429, 500)
- Поддерживает graceful degradation при отсутствии библиотеки httpx

### Файлы:
- `backend/app/integrations/ozon/get_product_list.py` - основная реализация интеграции
- `backend/app/integrations/ozon/__init__.py` - регистрация интеграции
- `backend/app/integrations/__init__.py` - добавлен импорт Ozon интеграций
- `backend/app/tests/integrations/test_ozon.py` - тесты интеграции
- `backend/app/tests/integrations/TEST_CASES_OZON.md` - документация по тестам

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
```

2. **Настроить Ozon credentials:**
   - Получить `Client-Id` и `Api-Key` в личном кабинете Ozon
   - Добавить credentials в систему через API или UI:
     ```json
     {
       "provider": "ozon",
       "strategy": "api_key",
       "payload": {
         "client_id": "YOUR_CLIENT_ID",
         "api_key": "YOUR_API_KEY"
       }
     }
     ```

### Тестирование через API:

1. **Получить каталог интеграций:**
```bash
curl -X GET "http://localhost:8003/api/integrations/catalog?category=ecommerce" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

2. **Получить метаданные интеграции:**
```bash
curl -X GET "http://localhost:8003/api/integrations/ozon_get_product_list/metadata" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

3. **Создать шаг с интеграцией:**
```bash
curl -X POST "http://localhost:8003/api/connection_groups/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "step_id": "YOUR_STEP_ID",
    "search_type": "integration",
    "integration_id": "ozon_get_product_list",
    "integration_config": {
      "limit": 100,
      "visibility": "ALL"
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

### Запуск unit тестов:

```bash
# Все тесты Ozon интеграции
pytest app/tests/integrations/test_ozon.py -v

# Конкретный тест
pytest app/tests/integrations/test_ozon.py::test_ozon_execute_success -v
```

### Ожидаемый результат:

- Интеграция успешно регистрируется в системе
- Метаданные корректно отображаются в каталоге
- Успешные запросы возвращают список товаров
- Ошибки обрабатываются корректно с понятными сообщениями
- Все тесты проходят успешно (11 тест-кейсов)

## Скриншоты (если применимо)

Не применимо — изменения касаются backend интеграции.

## Дополнительная информация

### API Ozon:

- **Base URL:** `https://api-seller.ozon.ru`
- **Endpoint:** `POST /v2/product/list`
- **Документация:** https://docs.ozon.ru/api/seller/

### Формат ответа (пример):

```json
{
  "result": {
    "items": [],
    "last_id": "0"
  },
  "total": 0
}
```

### Связанные файлы:

- `backend/app/integrations/ozon/get_product_list.py`
- `backend/app/tests/integrations/test_ozon.py`
- `backend/app/tests/integrations/TEST_CASES_OZON.md`
