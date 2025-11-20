# Архитектура проекта DBCV

## Обзор

DBCV - это NoCode/LowCode платформа для создания и управления ботами (агентами) через визуальный конструктор. Платформа позволяет создавать сложные диалоговые сценарии без программирования, используя систему шагов, связей и правил.

## Технологический стек

### Backend
- **FastAPI** - основной веб-фреймворк для REST API
- **FastStream** - асинхронная обработка сообщений через Redis Streams
- **SQLAlchemy (async)** - ORM для работы с базой данных
- **Alembic** - миграции базы данных
- **Pydantic** - валидация данных и схемы
- **Redis** - очереди сообщений и кэширование
- **PostgreSQL** - основная база данных
- **MinIO/S3** - хранилище файлов и медиа

### Дополнительные компоненты
- **MCP Server** - сервер для AI-ассистента (создание ботов через AI)
- **WebSocket** - real-time обновления для фронтенда
- **FastAdmin** - админ-панель

## Архитектура системы

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│              (HTML/JS визуальный конструктор)               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ HTTP/WebSocket
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                    FastAPI Backend                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   REST API   │  │  WebSocket   │  │   Admin      │     │
│  │   Routes     │  │   Routes     │  │   Panel      │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼──────┐ ┌────▼─────┐ ┌──────▼──────┐
│  PostgreSQL  │ │  Redis   │ │  MinIO/S3   │
│   Database   │ │ Streams  │ │  Storage    │
└──────────────┘ └──────────┘ └─────────────┘
        │              │
        │              │
┌───────▼──────────────▼──────────────────────┐
│         FastStream Workers                  │
│  ┌──────────────┐  ┌──────────────┐        │
│  │ User Worker  │  │  Bot Worker  │        │
│  │ (обработка   │  │  (обработка  │        │
│  │  сообщений   │  │   ответов    │        │
│  │  от юзеров)  │  │   от ботов)  │        │
│  └──────────────┘  └──────────────┘        │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │      Bot Processor Engine             │  │
│  │  (выполнение логики ботов)            │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

## Основные компоненты

### 1. FastAPI Backend (`backend/app/main.py`)

Основное приложение FastAPI, которое предоставляет:
- REST API endpoints для управления ботами, шагами, сообщениями
- WebSocket endpoints для real-time обновлений
- Admin панель для управления данными
- Статические файлы и медиа

**Ключевые маршруты:**
- `/api/v1/bots` - управление ботами
- `/api/v1/steps` - управление шагами
- `/api/v1/messages` - управление сообщениями
- `/api/v1/connections` - управление связями
- `/api/v1/requests` - управление HTTP запросами
- `/api/v1/templates` - управление шаблонами
- `/ws` - WebSocket соединения

### 2. FastStream Workers (`backend/app/faststream_app.py`)

Асинхронные воркеры для обработки сообщений через Redis Streams:

**User Worker** (`ROLE=user`):
- Подписывается на `user_messages` stream
- Обрабатывает входящие сообщения от пользователей
- Запускает логику ботов через `check_message()`

**Bot Worker** (`ROLE=bot`):
- Подписывается на `bot_messages` stream
- Обрабатывает исходящие сообщения от ботов
- Отправляет сообщения пользователям

**Особенности:**
- Batch обработка (до 100 сообщений за раз)
- Semaphore для ограничения параллелизма (DB_POOL_SIZE)
- Автоматический reclaim pending сообщений
- Consumer groups для масштабирования

### 3. Bot Processor Engine (`backend/app/engine/bot_processor.py`)

Ядро системы выполнения логики ботов:

**Основные классы:**

#### `Processor` (базовый класс)
- Управляет выполнением шагов
- Обрабатывает connection groups
- Выполняет переходы между шагами по правилам
- Сохраняет переменные

#### `MessageProcessor` (наследник Processor)
- Обрабатывает входящие сообщения
- Создает/обновляет сессии
- Запускает выполнение бота с текущего шага

#### `ConnectionHandler` (абстрактный)
Обработчики для разных типов connection groups:
- `ConnectionResponseHandler` - обработка HTTP запросов
- `ConnectionCodeHandler` - выполнение Python кода
- `ConnectionIntegrationHandler` - выполнение интеграций (будущее)

#### `CodeExecutor`
Безопасное выполнение Python кода:
- Ограниченный набор функций (`safe_globals`)
- Выполнение функции `main(message, variables)`
- Логирование ошибок

### 4. Data Manager (`backend/app/managers/data_manager.py`)

Менеджер для работы с данными:
- Кэширование в Redis
- Запросы к PostgreSQL
- Получение ботов, шагов, сессий, переменных
- Оптимизация через eager loading

**Ключевые методы:**
- `get_bot(bot_id)` - получение бота с кэшированием
- `get_step(step_id)` - получение шага
- `get_session(user_id, bot_id, channel_id)` - получение сессии
- `get_bot_variables(bot_id)` - переменные бота
- `get_user_variables(user_id)` - переменные пользователя

### 5. Models (База данных)

#### Основные модели:

**BotModel** (`backend/app/models/bot.py`)
- Представляет бота (агента)
- Связан с `first_step` (начальный шаг)
- Имеет переменные (`BotVariables`)
- Владелец (`owner_id`)

**StepModel** (`backend/app/models/step.py`)
- Шаг в диалоговом сценарии
- Может быть прокси (`is_proxy`) - автоматически переходит дальше
- Связан с сообщением (`message`)
- Имеет connection groups для переходов

**ConnectionGroupModel** (`backend/app/models/connection.py`)
- Группа связей для шага
- Типы: `response`, `message`, `code`, `integration` (будущее)
- Может содержать HTTP запрос (`request_id`)
- Может содержать Python код (`code`)
- Может содержать интеграцию (`integration_id`, `integration_config`)

**ConnectionModel**
- Связь между шагами
- Правила перехода (`rules`) - JSON с условиями
- Фильтры (`filters`)
- Приоритет (`priority`)
- Следующий шаг (`next_step_id`)

**MessageModel** (`backend/app/models/message.py`)
- Сообщение в диалоге
- Текст и параметры (JSON)
- Отправитель и получатель
- Прикрепления (attachments)
- Виджет (widget)

**SessionModel** (`backend/app/models/session.py`)
- Сессия пользователя с ботом
- Хранит текущий шаг (`step_id`)
- Переменные сессии (`SessionVariables`)
- Уникальна по комбинации (user_id, bot_id, channel_id)

**ChannelModel** (`backend/app/models/channel.py`)
- Канал коммуникации
- Имеет default_bot
- Подписчики (subscribers)
- Переменные канала (`ChannelVariables`)

**RequestModel** (`backend/app/models/request.py`)
- HTTP запрос для выполнения
- Метод, URL, headers, params, body
- Поддержка файлов (attachments)
- Прокси

**TemplateModel** (`backend/app/models/template.py`)
- Шаблон для переиспользования
- Входы/выходы (inputs/outputs)
- Переменные
- Шаги (JSON)

**TemplateInstanceModel**
- Экземпляр шаблона
- Маппинг входов/выходов
- Создает прокси-шаг

**CredentialEntity** (`backend/app/models/credentials.py`)
- Зашифрованные credentials для интеграций
- Provider (telegram, google, openai и т.д.)
- Strategy (api_key, oauth)
- Связан с ботом

### 6. Execution Flow (Поток выполнения)

```
1. Сообщение от пользователя
   ↓
2. FastStream Worker получает сообщение из Redis Stream
   ↓
3. check_message() определяет бота и канал
   ↓
4. MessageProcessor создает/обновляет сессию
   ↓
5. Получает текущий шаг из сессии
   ↓
6. Выполняет шаг:
   - Отправляет сообщение шага (если есть)
   - Обрабатывает connection groups
   ↓
7. Для каждого connection group:
   - ConnectionHandler обрабатывает (request/code/integration)
   - Сохраняет переменные
   - Проверяет rules в connections
   ↓
8. Если правило выполнено:
   - Переход на next_step
   - Обновление сессии
   - Повтор с шага 6
   ↓
9. Если шаг не proxy:
   - Ожидание следующего сообщения
```

### 7. Rules System (Система правил)

Правила для переходов между шагами используют JSON Query Builder (jqqb):

**Формат правила:**
```json
{
  "condition": "AND",
  "rules": [
    {
      "field": "message.text",
      "operator": "equals",
      "value": "start"
    }
  ]
}
```

**Операторы:**
- `equals`, `not_equals`
- `contains`, `not_contains`
- `greater_than`, `less_than`
- `in`, `not_in`
- И другие

**Оценка правил:**
- Правила проверяются через `Evaluator`
- Подстановка переменных перед проверкой
- Если правило пустое (`{}`) - всегда True (ELSE case)

### 8. Variables System (Система переменных)

Переменные доступны в формате `{scope}.{key}`:

**Scopes:**
- `bot.*` - переменные бота
- `user.*` - переменные пользователя
- `session.*` - переменные сессии
- `channel.*` - переменные канала
- `message.*` - данные сообщения

**Использование:**
- В текстах сообщений: `"Hello {$user.name$}!"`
- В правилах: `"message.text == '{$bot.command$}'"`
- В HTTP запросах: URL, headers, body
- В Python коде: `variables.get("user.name")`

### 9. Request System (Система HTTP запросов)

**RequestModel** позволяет выполнять HTTP запросы:
- Методы: GET, POST, PUT, DELETE и т.д.
- URL с подстановкой переменных
- Headers, params, body (JSON/form-data)
- Файлы (attachments)
- Прокси

**Выполнение:**
- Через `ConnectionResponseHandler`
- Использует `httpx.AsyncClient`
- Подстановка переменных перед запросом
- Результат сохраняется в context

### 10. Code Execution (Выполнение кода)

**Безопасное выполнение Python кода:**
- Ограниченный набор функций (`safe_globals`)
- Математические функции, datetime, json, re и т.д.
- Нет доступа к файловой системе, сети (кроме через Request)
- Функция должна быть: `async def main(message: dict | None, variables: dict)`

**Использование:**
- В connection groups с `search_type="code"`
- Генерация динамических данных
- Обработка данных перед запросом
- Сложная логика

### 11. Templates System (Система шаблонов)

**TemplateModel** - переиспользуемые структуры:
- Входы/выходы (JSON Schema)
- Переменные
- Шаги (JSON)

**TemplateInstanceModel** - экземпляр шаблона:
- Маппинг входов/выходов
- Создает прокси-шаг
- При выполнении заменяется на шаги шаблона

### 12. MCP Server (`backend/mcp/`)

MCP (Model Context Protocol) сервер для AI-ассистента:

**Назначение:**
- Создание ботов через AI
- Генерация шагов, связей, запросов
- Интеграция с AI моделями (OpenAI)

**Инструменты:**
- `create_bot` - создание бота
- `create_step` - создание шага
- `create_connection_group` - создание группы связей
- `create_request` - создание HTTP запроса
- И другие

**Реализация:**
- HTTP сервер (`http_server.py`)
- Обработка запросов от AI
- Вызов CRUD операций через API

### 13. Scheduler (`backend/app/scheduler.py`)

Планировщик для отложенных задач:
- **Emitter** - отложенная отправка сообщений
- **Cron** - периодические задачи
- Использует AsyncIOScheduler
- Подписывается на emitter stream

### 14. WebSocket (`backend/app/fast_socket_app.py`)

Real-time обновления для фронтенда:
- Подписка на каналы
- Уведомления о новых сообщениях
- Обновления ботов в реальном времени

## Будущие компоненты (в разработке)

### 1. Integrations System

**Назначение:** Готовые интеграции с внешними сервисами через библиотеки

**Структура:**
```
backend/app/integrations/
    base.py              # BaseIntegration
    registry.py          # IntegrationRegistry
    telegram/
        send_message.py  # Использует python-telegram-bot
    discord/
        execute_webhook.py  # Использует discord.py
    openai/
        chat_completion.py  # Использует openai
```

**Принцип работы:**
- Интеграции используют готовые библиотеки внутри backend кода
- Метод `execute()` вызывает методы библиотек
- Credentials получаются через `CredentialsResolver`
- Результат возвращается в формате системы

**Новый SearchType:**
- `SearchType.integration` - для connection groups с интеграциями
- `ConnectionIntegrationHandler` - обработчик интеграций

### 2. Presets System

**Назначение:** Готовые заготовки для типовых шагов

**Типы presets:**
- **IntegrationStepPreset** - шаг с интеграцией
- **ConditionalStepPreset** - IF/ELSE через rules
- **SwitchStepPreset** - SWITCH/CASE через множественные rules
- **DelayStepPreset** - задержка через code
- **MessageStepPreset** - простой шаг с сообщением
- **CodeStepPreset** - шаг с произвольным кодом

**Принцип работы:**
- Preset генерирует структуры (Step, ConnectionGroup, Connections)
- Сохраняет метаданные в Step (`preset_id`, `preset_icon_s3_key`)
- Фронтенд отображает иконку preset

### 3. Icon Service

**Назначение:** Управление иконками в S3

**Функции:**
- Загрузка SVG иконок в S3
- Получение публичных URL
- Иконки для интеграций и presets

## База данных

### Основные таблицы:

- `bot` - боты
- `step` - шаги
- `connection_group` - группы связей
- `connection` - связи между шагами
- `message` - сообщения
- `session` - сессии пользователей
- `session_variables` - переменные сессий
- `bot_variables` - переменные ботов
- `user_variables` - переменные пользователей
- `channel_variables` - переменные каналов
- `request` - HTTP запросы
- `template` - шаблоны
- `template_instance` - экземпляры шаблонов
- `channel` - каналы
- `subscriber` - подписчики (полиморфная модель)
- `user` - пользователи
- `anonymous_user` - анонимные пользователи
- `credential_entity` - credentials
- `attachment` - прикрепления
- `widget` - виджеты
- `note` - заметки
- `emitter` - отложенные сообщения
- `cron` - периодические задачи

### Связи:

- Bot → Steps (one-to-many)
- Step → ConnectionGroups (one-to-many)
- ConnectionGroup → Connections (one-to-many)
- Connection → NextStep (many-to-one)
- Step → Message (one-to-one)
- Session → Step (many-to-one)
- Bot → FirstStep (many-to-one)

## Docker Compose

Система развертывается через Docker Compose:

**Сервисы:**
- `backend` - FastAPI приложение
- `mcp-dbcv` - MCP сервер
- `postgres` - PostgreSQL база данных
- `redis` - Redis для очередей
- `cache-redis` - Redis для кэширования
- `faststream-bot` - Bot worker
- `faststream-user` - User worker
- `scheduler` - Планировщик задач
- `s3` - MinIO хранилище
- `s3-init` - Инициализация S3

## Безопасность

### Credentials:
- Хранение в зашифрованном виде (`CredentialEntity`)
- Использование `SecretBox` для шифрования
- Ключ шифрования в `SECRET_BOX_KEY`

### Code Execution:
- Ограниченный набор функций
- Нет доступа к файловой системе
- Нет прямого доступа к сети (только через Request)

### API:
- JWT токены для аутентификации
- Роли и права доступа
- CORS настройки

## Масштабирование

### Горизонтальное масштабирование:
- Несколько FastStream workers (user/bot)
- Consumer groups в Redis Streams
- Балансировка нагрузки через Redis

### Вертикальное масштабирование:
- Настройка DB_POOL_SIZE
- Настройка DB_MAX_OVERFLOW
- Semaphore для ограничения параллелизма

### Кэширование:
- Redis кэш для ботов, шагов, сессий
- DataManager с автоматическим кэшированием
- TTL для кэша

## Мониторинг

- Healthcheck endpoints (`/health`)
- Логирование через Python logging
- Метрики через WebSocket
- Redis мониторинг

## Разработка

### Структура проекта:
```
backend/
    app/
        api/          # REST API routes
        models/       # SQLAlchemy models
        schemas/      # Pydantic schemas
        crud/         # CRUD операции
        engine/       # Bot processor engine
        managers/     # Data managers
        services/     # Бизнес-логика
        auth/         # Аутентификация
        migrations/   # Alembic миграции
    mcp/              # MCP server
```

### Запуск:
```bash
docker-compose up -d
```

### Миграции:
```bash
alembic upgrade head
```

## Заключение

DBCV - это мощная платформа для создания ботов с гибкой архитектурой, которая позволяет:
- Создавать сложные диалоговые сценарии без программирования
- Использовать готовые интеграции с внешними сервисами
- Масштабироваться горизонтально
- Расширяться через presets и интеграции

Архитектура спроектирована для:
- Производительности (async, кэширование, batch обработка)
- Надежности (Redis Streams, consumer groups, reclaim)
- Расширяемости (интеграции, presets, templates)
- Безопасности (шифрование credentials, безопасный code execution)

