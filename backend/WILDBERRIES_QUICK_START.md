# 🚀 Wildberries Integration - Quick Start Guide

## ⚡ Быстрый старт (5 минут)

### 1. Установка Mock библиотеки

Mock библиотека уже создана в файле `wildberries_api.py`. Проверьте её наличие:

```bash
python -c "import wildberries_api; print('OK')"
```

Если видите `OK` - всё готово!

### 2. Запуск теста

**Вариант A: PowerShell (рекомендуется)**

```powershell
.\run_wildberries_improved.ps1
```

**Вариант B: Python напрямую**

```bash
python run_wildberries_test.py
```

**Ожидаемый результат:**

```
============================================================
🧪 Wildberries Integration Test (Registry Check)
============================================================

✅ Интеграция Wildberries успешно зарегистрирована!

📋 Метаданные интеграции:
   ID: wildberries_update_stock
   Версия: 1.0.0
   Название: Wildberries Update Stock
   ...
```

### 3. Первый запуск интеграции (DRY-RUN)

Создайте файл `.env`:

```bash
cp .env.example .env
```

Отредактируйте `.env`:

```env
WB_BOT_ID=12345678-1234-1234-1234-123456789012
WB_TEST_SKU=TEST-SKU-001
WB_TEST_STOCK=100
WB_DRY_RUN=true
```

Запустите:

```bash
python run_wildberries_integration.py
```

---

## 📋 Что включено

### Файлы интеграции

```
DBCV/backend/
├── app/
│   └── integrations/
│       └── Wildberries/
│           ├── __init__.py
│           └── update_stock.py          # Основной класс интеграции
│
├── wildberries_api.py                   # Mock библиотека для тестирования
├── run_wildberries_test.py              # Тест регистрации (улучшенный)
├── run_wildberries_integration.py       # Запуск интеграции
├── minimal_wb_test.py                   # Минимальный тест структуры
├── run_wildberries.ps1                  # PowerShell скрипт (базовый)
├── run_wildberries_improved.ps1         # PowerShell скрипт (улучшенный)
├── .env.example                         # Пример конфигурации
└── WILDBERRIES_INTEGRATION_GUIDE.md     # Полная документация
```

### Основные возможности

✅ **Регистрация в реестре интеграций**
- Автоматическая регистрация при старте
- Метаданные с полным описанием
- Схема валидации конфигурации

✅ **Обновление остатков**
- По артикулу (SKU)
- С указанием количества (stock)
- Поддержка нескольких складов (warehouse_id)

✅ **Безопасность**
- Получение credentials из БД
- Валидация входных данных
- Обработка всех типов ошибок

✅ **Логирование**
- Детальные логи всех операций
- Уровни: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Вывод в консоль и файл (опционально)

✅ **Тестирование**
- Mock библиотека для разработки
- Dry-run режим
- Множественные тесты

---

## 🧪 Режимы тестирования

### Режим 1: Registry Test

**Что проверяет:**
- Регистрация интеграции в реестре
- Корректность метаданных
- Наличие всех необходимых полей

**Запуск:**
```bash
python run_wildberries_test.py
```

### Режим 2: Structure Test

**Что проверяет:**
- Структура файлов интеграции
- Наличие обязательных методов
- Импорты зависимостей

**Запуск:**
```bash
python minimal_wb_test.py
```

### Режим 3: Dry-Run

**Что делает:**
- Проверяет конфигурацию
- Валидирует параметры
- НЕ выполняет реальные API запросы

**Запуск:**
```bash
# В .env установите:
WB_DRY_RUN=true

python run_wildberries_integration.py
```

### Режим 4: Mock Execution

**Что делает:**
- Использует mock библиотеку
- Имитирует API запросы
- Возвращает тестовые данные

**Запуск:**
```bash
# Убедитесь что wildberries_api.py доступен
python run_wildberries_integration.py
```

---

## 🔧 Конфигурация

### Переменные окружения (.env)

```env
# === BOT CONFIGURATION ===
WB_BOT_ID=12345678-1234-1234-1234-123456789012

# === TEST DATA ===
WB_TEST_SKU=TEST-SKU-001
WB_TEST_STOCK=100
WB_TEST_WAREHOUSE_ID=

# === DATABASE ===
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname

# === LOGGING ===
LOG_LEVEL=INFO
LOG_TO_FILE=false
LOG_FILE_PATH=logs/wildberries_integration.log

# === EXECUTION MODE ===
WB_DRY_RUN=true
```

### Параметры интеграции

#### Обязательные:
- `sku` (string) - Артикул товара
- `stock` (integer, >= 0) - Количество на складе

#### Опциональные:
- `warehouse_id` (string) - ID склада

### Пример конфигурации для execute:

```python
config = {
    "sku": "WB12345",
    "stock": 50,
    "warehouse_id": "WAREHOUSE-001"  # опционально
}
```

---

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
      "sku": "WB12345",
      "stock": 50,
      "updated": true,
      "timestamp": 1234567890,
      "message": "Stock updated successfully for SKU WB12345"
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

---

## 🔐 Credentials

### Формат в базе данных:

```json
{
  "payload": {
    "api_key": "your-wildberries-api-key-here"
  }
}
```

### SQL для добавления:

```sql
INSERT INTO credentials (bot_id, provider, strategy, payload)
VALUES (
    '12345678-1234-1234-1234-123456789012',
    'wildberries',
    'api_key',
    '{"api_key": "your-api-key-here"}'::jsonb
);
```

---

## ❌ Типичные ошибки и решения

### Ошибка: "Integration not found"

**Причина:** Интеграция не зарегистрирована

**Решение:**
```bash
# Проверьте регистрацию
python run_wildberries_test.py

# Перезапустите приложение
```

### Ошибка: "wildberries_api library is not available"

**Причина:** Mock библиотека не найдена

**Решение:**
```bash
# Проверьте наличие файла
ls wildberries_api.py

# Проверьте импорт
python -c "import wildberries_api; print('OK')"
```

### Ошибка: "Credentials not found"

**Причина:** Нет credentials в БД для bot_id

**Решение:**
```sql
-- Проверьте наличие
SELECT * FROM credentials 
WHERE bot_id = 'your-bot-id' 
  AND provider = 'wildberries'
  AND strategy = 'api_key';

-- Добавьте если нет
INSERT INTO credentials (...) VALUES (...);
```

### Ошибка: "Database connection failed"

**Причина:** БД недоступна или неверная конфигурация

**Решение:**
```bash
# Проверьте DATABASE_URL в .env
# Убедитесь что PostgreSQL запущен
pg_isready -h localhost -p 5432

# Проверьте подключение
psql -h localhost -U user -d dbname
```

---

## 📝 Примеры использования

### Пример 1: Базовое обновление

```python
import asyncio
from uuid import UUID
from app.integrations.registry import registry

async def update_stock():
    integration = registry.get("wildberries_update_stock")
    
    result = await integration.execute(
        config={
            "sku": "WB12345",
            "stock": 50
        },
        credentials_resolver=credentials_resolver,
        bot_id=UUID("12345678-1234-1234-1234-123456789012"),
        logger=logger
    )
    
    print(result)

asyncio.run(update_stock())
```

### Пример 2: С указанием склада

```python
result = await integration.execute(
    config={
        "sku": "WB12345",
        "stock": 50,
        "warehouse_id": "WAREHOUSE-001"
    },
    credentials_resolver=credentials_resolver,
    bot_id=bot_id,
    logger=logger
)
```

### Пример 3: Массовое обновление

```python
skus = [
    {"sku": "WB001", "stock": 10},
    {"sku": "WB002", "stock": 20},
    {"sku": "WB003", "stock": 30}
]

for item in skus:
    result = await integration.execute(
        config=item,
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    print(f"{item['sku']}: {result['response']['ok']}")
```

---

## 🎯 Следующие шаги

1. ✅ **Запустите тест регистрации**
   ```bash
   python run_wildberries_test.py
   ```

2. ✅ **Настройте .env файл**
   ```bash
   cp .env.example .env
   # Отредактируйте .env
   ```

3. ✅ **Добавьте credentials в БД**
   ```sql
   INSERT INTO credentials (...) VALUES (...);
   ```

4. ✅ **Запустите в dry-run режиме**
   ```bash
   python run_wildberries_integration.py
   ```

5. ✅ **Запустите с реальными данными**
   ```bash
   # Установите WB_DRY_RUN=false в .env
   python run_wildberries_integration.py
   ```

---

## 📚 Дополнительная документация

- **Полное руководство:** `WILDBERRIES_INTEGRATION_GUIDE.md`
- **Исходный код:** `app/integrations/Wildberries/update_stock.py`
- **Mock библиотека:** `wildberries_api.py`
- **Тесты:** `run_wildberries_test.py`, `minimal_wb_test.py`

---

**Версия:** 1.0.0  
**Статус:** ✅ Ready for testing  
**Автор:** DBCV Team
