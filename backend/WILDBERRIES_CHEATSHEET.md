# 🚀 Wildberries Integration - Cheat Sheet

## Быстрая справка по командам и конфигурации

---

## ⚡ Команды (Quick Reference)

### Тестирование

```bash
# Тест регистрации интеграции
python run_wildberries_test.py

# Минимальный тест структуры (без БД)
python minimal_wb_test.py

# Dry-run (без реальных API вызовов)
WB_DRY_RUN=true python run_wildberries_integration.py

# PowerShell меню
.\run_wildberries_improved.ps1
```

### Запуск интеграции

```bash
# Интерактивный режим
python run_wildberries_integration.py

# С переменными окружения
python run_wildberries_integration.py  # читает из .env

# PowerShell
.\run_wildberries.ps1
```

### Проверка зависимостей

```bash
# Проверка mock библиотеки
python -c "import wildberries_api; print('OK')"

# Версия библиотеки
python -c "import wildberries_api; print(wildberries_api.__version__)"

# Проверка интеграции
python -c "from app.integrations.registry import registry; print(registry.get('wildberries_update_stock'))"
```

---

## 📋 Конфигурация .env

```env
# === ОБЯЗАТЕЛЬНЫЕ ===
WB_BOT_ID=12345678-1234-1234-1234-123456789012
WB_TEST_SKU=TEST-SKU-001
WB_TEST_STOCK=100

# === ОПЦИОНАЛЬНЫЕ ===
WB_TEST_WAREHOUSE_ID=WAREHOUSE-001
WB_DRY_RUN=true

# === БАЗА ДАННЫХ ===
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# === ЛОГИРОВАНИЕ ===
LOG_LEVEL=INFO                                    # DEBUG|INFO|WARNING|ERROR
LOG_TO_FILE=false                                 # true|false
LOG_FILE_PATH=logs/wildberries_integration.log
```

---

## 🔐 Credentials в БД

### SQL для добавления

```sql
INSERT INTO credentials (bot_id, provider, strategy, payload)
VALUES (
    '12345678-1234-1234-1234-123456789012',
    'wildberries',
    'api_key',
    '{"api_key": "your-api-key-here"}'::jsonb
);
```

### SQL для проверки

```sql
SELECT * FROM credentials 
WHERE provider = 'wildberries' 
  AND strategy = 'api_key';
```

---

## 📊 Формат данных

### Конфигурация для execute()

```python
config = {
    "sku": "WB12345",           # Обязательно
    "stock": 50,                # Обязательно (>= 0)
    "warehouse_id": "WH001"    # Опционально
}
```

### Успешный ответ

```json
{
  "response": {
    "ok": true,
    "result": {
      "sku": "WB12345",
      "stock": 50,
      "updated": true
    }
  }
}
```

### Ответ с ошибкой

```json
{
  "response": {
    "ok": false,
    "error_code": 401,
    "description": "Authentication failed"
  }
}
```

---

## 🐍 Python код

### Базовое использование

```python
import asyncio
from uuid import UUID
from app.integrations.registry import registry

async def update_stock():
    integration = registry.get("wildberries_update_stock")
    
    result = await integration.execute(
        config={"sku": "WB12345", "stock": 50},
        credentials_resolver=credentials_resolver,
        bot_id=UUID("12345678-1234-1234-1234-123456789012"),
        logger=logger
    )
    
    if result["response"]["ok"]:
        print("✅ Success")
    else:
        print(f"❌ Error: {result['response']['description']}")

asyncio.run(update_stock())
```

### Mock библиотека

```python
from wildberries_api import Client

# Создание клиента
client = Client(api_key="test-key")

# Обновление остатков
result = client.update_stock(
    sku="TEST-001",
    stock=100,
    warehouse_id="WH001"  # опционально
)

print(result)
# {'sku': 'TEST-001', 'stock': 100, 'updated': True, ...}
```

---

## 📁 Структура файлов

```
DBCV/backend/
├── app/integrations/Wildberries/
│   └── update_stock.py              # Основная интеграция
├── wildberries_api.py               # Mock библиотека
├── run_wildberries_test.py          # Тест регистрации
├── run_wildberries_integration.py   # Запуск интеграции
├── minimal_wb_test.py               # Минимальный тест
├── run_wildberries.ps1              # PowerShell (базовый)
├── run_wildberries_improved.ps1     # PowerShell (с меню)
└── .env.example                     # Пример конфигурации
```

---

## 🔧 Типичные проблемы

| Ошибка | Причина | Решение |
|--------|---------|----------|
| Integration not found | Не зарегистрирована | `python run_wildberries_test.py` |
| wildberries_api not available | Библиотека не найдена | Проверьте `wildberries_api.py` |
| Credentials not found | Нет в БД | Добавьте SQL командой |
| Database connection failed | БД недоступна | Проверьте DATABASE_URL |
| Invalid UUID | Неверный формат | Используйте UUID формат |
| Invalid stock value | Отрицательное число | stock >= 0 |

---

## 🎯 Workflow

### Первый запуск

```bash
# 1. Проверка файлов
ls wildberries_api.py

# 2. Тест регистрации
python run_wildberries_test.py

# 3. Настройка .env
cp .env.example .env
# Отредактируйте .env

# 4. Dry-run
WB_DRY_RUN=true python run_wildberries_integration.py
```

### Разработка

```bash
# 1. Минимальный тест (без БД)
python minimal_wb_test.py

# 2. Mock библиотека
python -c "from wildberries_api import Client; c = Client('test'); print(c.update_stock('SKU', 10))"

# 3. Изменения в коде
# Редактируйте app/integrations/Wildberries/update_stock.py

# 4. Тест после изменений
python run_wildberries_test.py
```

### Production

```bash
# 1. Добавить credentials в БД
psql -h host -U user -d db -c "INSERT INTO credentials ..."

# 2. Настроить .env для production
WB_DRY_RUN=false
LOG_LEVEL=WARNING
LOG_TO_FILE=true

# 3. Тест с реальными данными
python run_wildberries_integration.py

# 4. Мониторинг
tail -f logs/wildberries_integration.log
```

---

## 💻 PowerShell команды

### Базовый скрипт

```powershell
# Запуск
.\run_wildberries.ps1

# Принудительный запуск
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run_wildberries.ps1
```

### Улучшенный скрипт

```powershell
# Запуск с меню
.\run_wildberries_improved.ps1

# Опции:
# 1 - С переменными окружения
# 2 - Интерактивный режим
# 3 - Минимальный тест
# 4 - Выход
```

---

## 📚 Документация (быстрые ссылки)

- **Quick Start:** `WILDBERRIES_QUICK_START.md`
- **README:** `WILDBERRIES_README.md`
- **Full Guide:** `WILDBERRIES_INTEGRATION_GUIDE.md`
- **Improvements:** `WILDBERRIES_IMPROVEMENTS_SUMMARY.md`
- **Index:** `WILDBERRIES_INDEX.md`

---

## 🔍 Debugging

### Проверка импортов

```python
# Проверка registry
python -c "from app.integrations.registry import registry; print(len(registry.list_all()))"

# Проверка интеграции
python -c "from app.integrations.Wildberries.update_stock import WildberriesUpdateStockIntegration; print('OK')"

# Проверка mock библиотеки
python -c "import wildberries_api; print(wildberries_api.__version__)"
```

### Логирование

```python
# Включить DEBUG логи
import logging
logging.basicConfig(level=logging.DEBUG)

# В .env
LOG_LEVEL=DEBUG
```

### Проверка БД

```sql
-- Список credentials
SELECT bot_id, provider, strategy FROM credentials;

-- Проверка payload
SELECT payload FROM credentials 
WHERE provider = 'wildberries';
```

---

## 🎨 Exit Codes

| Code | Значение | Когда |
|------|----------|-------|
| 0 | Success | Все ОК |
| 1 | Error | Общая ошибка |
| 130 | Interrupted | Ctrl+C / KeyboardInterrupt |

---

## 🚦 Статусы ответа

| HTTP Code | Значение | Действие |
|-----------|----------|----------|
| 200 | OK | Успех |
| 400 | Bad Request | Проверить данные |
| 401 | Unauthorized | Проверить API key |
| 404 | Not Found | SKU не найден |
| 500 | Server Error | Повторить позже |
| 504 | Timeout | Увеличить timeout |

---

## 📦 Версии

```bash
# Проверка версии Python
python --version  # Требуется 3.11+

# Проверка версии библиотек
pip show fastapi sqlalchemy asyncpg

# Проверка версии mock библиотеки
python -c "import wildberries_api; print(wildberries_api.__version__)"
```

---

## 🎯 Полезные алиасы (Bash)

```bash
# Добавьте в ~/.bashrc
alias wb-test='python run_wildberries_test.py'
alias wb-run='python run_wildberries_integration.py'
alias wb-dry='WB_DRY_RUN=true python run_wildberries_integration.py'
alias wb-logs='tail -f logs/wildberries_integration.log'
```

## 🎯 Полезные алиасы (PowerShell)

```powershell
# Добавьте в $PROFILE
function wb-test { python run_wildberries_test.py }
function wb-run { python run_wildberries_integration.py }
function wb-dry { $env:WB_DRY_RUN='true'; python run_wildberries_integration.py }
function wb-menu { .\run_wildberries_improved.ps1 }
```

---

**Версия:** 1.0.0  
**Последнее обновление:** 2024
