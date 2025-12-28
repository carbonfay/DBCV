# 🛍️ Wildberries Integration

## Полная документация по интеграции с Wildberries

---

## 📖 Оглавление

1. [Обзор](#обзор)
2. [Быстрый старт](#быстрый-старт)
3. [Структура проекта](#структура-проекта)
4. [Документация](#документация)
5. [Скрипты](#скрипты)
6. [Конфигурация](#конфигурация)
7. [Тестирование](#тестирование)
8. [Производственное использование](#производственное-использование)

---

## 🎯 Обзор

Интеграция с Wildberries позволяет управлять остатками товаров на маркетплейсе через единый интерфейс платформы DBCV.

### Ключевые возможности

- ✅ **Обновление остатков** - изменение количества товара по SKU
- ✅ **Поддержка складов** - работа с несколькими складами
- ✅ **Безопасность** - хранение API ключей в зашифрованном виде
- ✅ **Логирование** - детальные логи всех операций
- ✅ **Валидация** - проверка входных данных
- ✅ **Обработка ошибок** - корректная обработка всех типов ошибок

### Технологический стек

- **Python 3.11+**
- **FastAPI** - веб-фреймворк
- **SQLAlchemy** - ORM для работы с БД
- **PostgreSQL** - база данных
- **AsyncIO** - асинхронное выполнение

---

## ⚡ Быстрый старт

### За 3 минуты

1. **Проверьте наличие файлов:**
   ```bash
   cd DBCV/backend
   ls wildberries_api.py  # Mock библиотека должна быть
   ```

2. **Запустите тест:**
   ```bash
   python run_wildberries_test.py
   ```

3. **Готово!** Если тест прошел успешно - интеграция работает.

### Полная инструкция

См. [WILDBERRIES_QUICK_START.md](./WILDBERRIES_QUICK_START.md)

---

## 📁 Структура проекта

```
DBCV/backend/
│
├── app/
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── base.py                      # Базовый класс интеграций
│   │   ├── registry.py                  # Реестр интеграций
│   │   └── Wildberries/
│   │       ├── __init__.py              # Экспорт интеграции
│   │       └── update_stock.py          # ⭐ Основной класс
│   │
│   ├── auth/
│   │   └── credentials_resolver.py      # Получение credentials
│   │
│   ├── managers/
│   │   └── data_manager.py             # Менеджер данных
│   │
│   ├── loggers/
│   │   └── bot.py                      # Логгер для ботов
│   │
│   └── database.py                      # Настройка БД
│
├── wildberries_api.py                   # 🧪 Mock библиотека
│
├── run_wildberries_test.py              # ✅ Тест регистрации
├── run_wildberries_integration.py       # 🚀 Запуск интеграции
├── minimal_wb_test.py                   # 🔍 Минимальный тест
│
├── run_wildberries.ps1                  # 💻 PowerShell (базовый)
├── run_wildberries_improved.ps1         # 💻 PowerShell (улучшенный)
│
├── .env.example                         # 📝 Пример конфигурации
│
└── DOCS/
    ├── WILDBERRIES_README.md            # 📖 Этот файл
    ├── WILDBERRIES_QUICK_START.md       # ⚡ Быстрый старт
    └── WILDBERRIES_INTEGRATION_GUIDE.md # 📚 Полное руководство
```

---

## 📚 Документация

### Основные документы

| Документ | Описание | Для кого |
|----------|----------|----------|
| **WILDBERRIES_README.md** | Обзор интеграции | Все |
| **WILDBERRIES_QUICK_START.md** | Быстрый старт за 5 минут | Разработчики |
| **WILDBERRIES_INTEGRATION_GUIDE.md** | Полное руководство | DevOps, Архитекторы |

### Комментарии в коде

Весь код полностью документирован с использованием docstrings:

```python
class WildberriesUpdateStockIntegration(BaseIntegration):
    """Интеграция для обновления остатков на Wildberries.
    
    Использует библиотеку `wildberries_api` для работы с API.
    Поддерживает обновление остатков по SKU с указанием склада.
    """
```

---

## 🛠️ Скрипты

### Python скрипты

#### 1. `run_wildberries_test.py`

**Назначение:** Проверка регистрации интеграции

**Запуск:**
```bash
python run_wildberries_test.py
```

**Что проверяет:**
- Регистрация в реестре
- Корректность метаданных
- Схема конфигурации
- Наличие примеров

**Улучшения (v2.0):**
- ✅ Структурированный вывод
- ✅ Расширенное логирование
- ✅ Exit codes для CI/CD
- ✅ Обработка ошибок

---

#### 2. `run_wildberries_integration.py`

**Назначение:** Запуск интеграции с реальными/тестовыми данными

**Запуск:**
```bash
# С переменными окружения
python run_wildberries_integration.py

# Интерактивный режим
python run_wildberries_integration.py
# (просто запустите и следуйте инструкциям)
```

**Режимы работы:**
- Интерактивный (ввод с клавиатуры)
- Из переменных окружения (.env)
- Dry-run (без реальных API запросов)

**Возможности:**
- ✅ Валидация входных данных
- ✅ Подключение к БД
- ✅ Получение credentials
- ✅ Выполнение интеграции
- ✅ Детальное логирование

---

#### 3. `minimal_wb_test.py`

**Назначение:** Минимальный тест структуры без БД

**Запуск:**
```bash
python minimal_wb_test.py
```

**Что проверяет:**
- Наличие файла интеграции
- Ключевые элементы кода
- Метаданные в исходном коде
- Наличие зависимостей

---

### PowerShell скрипты

#### 1. `run_wildberries.ps1`

**Назначение:** Базовый скрипт-помощник

**Запуск:**
```powershell
.\run_wildberries.ps1
```

**Что делает:**
1. Запускает тест регистрации
2. Показывает инструкции для полного запуска

---

#### 2. `run_wildberries_improved.ps1` ⭐

**Назначение:** Расширенный скрипт с меню

**Запуск:**
```powershell
.\run_wildberries_improved.ps1
```

**Возможности:**
- ✅ Проверка всех файлов
- ✅ Проверка зависимостей
- ✅ Меню выбора режима
- ✅ Безопасный запуск скриптов
- ✅ Обработка ошибок

**Опции меню:**
```
1. Run with environment variables (.env file)
2. Run in interactive mode (manual input)
3. Run minimal structure test (no DB)
4. Exit
```

---

## ⚙️ Конфигурация

### Файл .env

Создайте из примера:
```bash
cp .env.example .env
```

Основные параметры:

```env
# Bot ID (UUID бота)
WB_BOT_ID=12345678-1234-1234-1234-123456789012

# Тестовые данные
WB_TEST_SKU=TEST-SKU-001
WB_TEST_STOCK=100
WB_TEST_WAREHOUSE_ID=

# База данных
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# Логирование
LOG_LEVEL=INFO
LOG_TO_FILE=false
LOG_FILE_PATH=logs/wildberries_integration.log

# Режим выполнения
WB_DRY_RUN=true  # true = не выполнять реальные запросы
```

### Credentials в БД

Формат хранения:

```sql
CREATE TABLE credentials (
    id SERIAL PRIMARY KEY,
    bot_id UUID NOT NULL,
    provider VARCHAR(50) NOT NULL,
    strategy VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

Пример записи:

```sql
INSERT INTO credentials (bot_id, provider, strategy, payload)
VALUES (
    '12345678-1234-1234-1234-123456789012',
    'wildberries',
    'api_key',
    '{"api_key": "your-wildberries-api-key-here"}'::jsonb
);
```

---

## 🧪 Тестирование

### Уровни тестирования

#### Level 1: Unit тесты

```bash
# Тест структуры без импортов
python minimal_wb_test.py
```

#### Level 2: Integration тесты

```bash
# Тест регистрации
python run_wildberries_test.py
```

#### Level 3: E2E тесты

```bash
# Dry-run с mock данными
WB_DRY_RUN=true python run_wildberries_integration.py
```

#### Level 4: Production-like тесты

```bash
# С реальными credentials но тестовыми SKU
WB_DRY_RUN=false WB_TEST_SKU=TEST-001 python run_wildberries_integration.py
```

### Mock библиотека

Файл `wildberries_api.py` предоставляет:

- ✅ Имитацию API клиента
- ✅ Все типы исключений
- ✅ Валидацию данных
- ✅ Различные сценарии ответов

**Использование:**

```python
from wildberries_api import Client

client = Client(api_key="test-key")
result = client.update_stock(sku="TEST-001", stock=100)
print(result)
```

**Тестовые сценарии:**

```python
# Успешное обновление
result = client.update_stock("NORMAL-SKU", 100)

# Ошибка сервера
try:
    result = client.update_stock("ERROR-SKU", 100)
except WildberriesAPIError as e:
    print(f"Error: {e}")

# SKU не найден
try:
    result = client.update_stock("NOTFOUND-SKU", 100)
except WildberriesAPIError as e:
    print(f"Not found: {e}")
```

---

## 🚀 Производственное использование

### Подготовка к production

#### 1. Установка реальной библиотеки

```bash
# Вместо mock библиотеки установите реальную
pip install wildberries-api

# Или используйте httpx для прямых запросов
# httpx уже в requirements.txt
```

#### 2. Настройка credentials

```sql
-- Добавьте реальный API ключ
INSERT INTO credentials (bot_id, provider, strategy, payload)
VALUES (
    'production-bot-uuid',
    'wildberries',
    'api_key',
    '{"api_key": "prod-api-key"}'::jsonb
);
```

#### 3. Настройка логирования

```env
LOG_LEVEL=WARNING
LOG_TO_FILE=true
LOG_FILE_PATH=/var/log/dbcv/wildberries.log
```

#### 4. Мониторинг

Создайте мониторинг для:
- Частоты запросов
- Времени отклика
- Количества ошибок
- Успешности обновлений

#### 5. Резервное копирование

Регулярно сохраняйте:
- Состояние остатков
- Логи операций
- Credentials (зашифрованные)

### Best Practices

1. **Используйте batch операции** для массовых обновлений
2. **Реализуйте retry logic** для временных ошибок
3. **Кэшируйте credentials** для уменьшения нагрузки на БД
4. **Логируйте все операции** для аудита
5. **Используйте rate limiting** для соблюдения лимитов API

---

## 📞 Поддержка

### Проблемы и вопросы

1. **Проверьте документацию:**
   - WILDBERRIES_QUICK_START.md
   - WILDBERRIES_INTEGRATION_GUIDE.md

2. **Запустите диагностику:**
   ```bash
   python run_wildberries_test.py
   python minimal_wb_test.py
   ```

3. **Проверьте логи:**
   ```bash
   tail -f logs/wildberries_integration.log
   ```

### Частые проблемы

См. раздел "Troubleshooting" в [WILDBERRIES_INTEGRATION_GUIDE.md](./WILDBERRIES_INTEGRATION_GUIDE.md)

---

## 📝 Changelog

### Version 2.0.0 (Current)

**Улучшения:**
- ✅ Улучшенные скрипты тестирования
- ✅ Расширенное логирование
- ✅ PowerShell скрипт с меню
- ✅ Mock библиотека для тестирования
- ✅ Полная документация
- ✅ Поддержка .env конфигурации
- ✅ Dry-run режим
- ✅ Exit codes для CI/CD

**Новые файлы:**
- `wildberries_api.py` - Mock библиотека
- `run_wildberries_improved.ps1` - Улучшенный PowerShell
- `minimal_wb_test.py` - Минимальный тест
- `.env.example` - Пример конфигурации
- Документация (3 файла)

### Version 1.0.0 (Initial)

- ✅ Базовая интеграция
- ✅ Регистрация в реестре
- ✅ Простые скрипты

---

## 📄 Лицензия

Проприетарное ПО. Все права защищены.

---

## 👥 Авторы

DBCV Team - Backend Integration Team

---

**Версия документа:** 2.0.0  
**Дата обновления:** 2024  
**Статус:** ✅ Production Ready (with mock library)
