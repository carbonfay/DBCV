# 🔧 Руководство по запуску интеграции Wildberries

## 📋 Описание

Интеграция **Wildberries Update Stock** позволяет обновлять остатки товаров на платформе Wildberries через их API.

## 🚀 Способы запуска

### 1. Проверка регистрации интеграции

Простой скрипт для проверки, что интеграция корректно зарегистрирована:

```bash
cd DBCV/backend
python test_wildberries_registration.py
```

или

```bash
python run_wildberries_test.py
```

**Что проверяется:**
- ✅ Интеграция найдена в реестре
- ✅ Метаданные загружены корректно
- ✅ Схема конфигурации валидна
- ✅ Библиотека `wildberries-api` указана

### 2. Запуск интеграции (интерактивный режим)

Для реального выполнения запроса к API Wildberries:

```bash
python run_wildberries_integration.py
```

**Потребуется ввести:**
1. `BOT_ID` - UUID бота из базы данных
2. `SKU` - артикул товара на Wildberries
3. `Stock` - количество товара на складе
4. `Warehouse ID` - ID склада (опционально)

### 3. Запуск через API

Интеграция автоматически доступна через API после регистрации:

**Эндпоинт:** `POST /api/v1/integrations/execute`

**Пример запроса:**

```json
{
  "integration_id": "wildberries_update_stock",
  "bot_id": "your-bot-uuid",
  "config": {
    "sku": "WB12345",
    "stock": 50,
    "warehouse_id": "optional-warehouse-id"
  }
}
```

## 🔐 Настройка credentials

Перед запуском необходимо добавить API-ключ Wildberries в базу данных:

### Через админ-панель

1. Откройте админ-панель: http://localhost:8003/admin
2. Перейдите в раздел **Credentials**
3. Создайте новую запись:
   - **Bot ID**: UUID вашего бота
   - **Provider**: `wildberries`
   - **Strategy**: `api_key`
   - **Payload**: 
     ```json
     {
       "api_key": "ваш-api-ключ-wildberries"
     }
     ```
   - **Is Default**: ✓ (отметьте галочку)

### Через SQL (альтернатива)

```sql
INSERT INTO credentials (bot_id, provider, strategy, payload, is_default)
VALUES (
  'ваш-bot-uuid',
  'wildberries',
  'api_key',
  '{"api_key": "ваш-api-ключ"}',
  true
);
```

## 📦 Зависимости

Убедитесь, что установлена библиотека:

```bash
pip install wildberries-api>=1.2.0
```

или установите все зависимости интеграций:

```bash
pip install -r requirements_integrations.txt
```

## 🧪 Структура конфигурации

### Обязательные параметры:

- **sku** (string): Артикул товара на Wildberries
- **stock** (integer): Количество на складе (>= 0)

### Опциональные параметры:

- **warehouse_id** (string): ID склада

### Пример валидной конфигурации:

```json
{
  "sku": "WB12345",
  "stock": 100,
  "warehouse_id": "warehouse_1"
}
```

## 📊 Формат ответа

### Успешный ответ:

```json
{
  "response": {
    "ok": true,
    "error_code": null,
    "description": null,
    "error": null,
    "result": {
      "updated": true,
      "sku": "WB12345",
      "new_stock": 100
    }
  }
}
```

### Ответ с ошибкой:

```json
{
  "response": {
    "ok": false,
    "error_code": 401,
    "description": "Authentication failed",
    "error": "Invalid API key",
    "result": null
  }
}
```

## 🔍 Отладка

### Логи

Все действия интеграции логируются через `BotLogger`. Проверьте логи:

```bash
# В режиме разработки логи выводятся в консоль
tail -f logs/app.log
```

### Типичные ошибки

**1. "wildberries_api library is not available"**
- Решение: установите `pip install wildberries-api>=1.2.0`

**2. "Wildberries api_key not found in credentials"**
- Решение: добавьте credentials в БД (см. раздел "Настройка credentials")

**3. "Authentication failed"**
- Решение: проверьте корректность API-ключа

**4. "API request timed out"**
- Решение: проверьте сетевое соединение и доступность API Wildberries

## 🛠️ Примеры использования

### Пример 1: Обновление остатка товара

```python
from app.integrations.registry import registry
from uuid import UUID

# Получаем интеграцию
integration = registry.get("wildberries_update_stock")

# Конфигурация
config = {
    "sku": "WB12345",
    "stock": 75
}

# Выполнение
result = await integration.execute(
    config=config,
    credentials_resolver=credentials_resolver,
    bot_id=UUID("your-bot-id"),
    logger=logger
)
```

### Пример 2: Обнуление остатков

```python
config = {
    "sku": "WB67890",
    "stock": 0
}
```

### Пример 3: С указанием склада

```python
config = {
    "sku": "WB11111",
    "stock": 150,
    "warehouse_id": "MSK_WAREHOUSE_1"
}
```

## 📚 Дополнительные ресурсы

- [Документация Wildberries API](https://openapi.wildberries.ru/)
- [Библиотека wildberries-api](https://pypi.org/project/wildberries-api/)

## 🆘 Поддержка

При возникновении проблем:
1. Проверьте логи интеграции
2. Убедитесь, что credentials настроены корректно
3. Проверьте доступность API Wildberries
4. Проверьте формат конфигурации

---

**Версия:** 1.0.0  
**Последнее обновление:** 2024