# DBCV - Документация

## Оглавление

1. [Введение](#введение)
2. [Быстрый старт](#быстрый-старт)
3. [API Endpoints](#api-endpoints)
4. [Работа с ботами](#работа-с-ботами)
5. [Система шагов](#система-шагов)
6. [Система переменных](#система-переменных)
7. [Правила (Rules)](#правила-rules)
8. [HTTP запросы](#http-запросы)
9. [Выполнение кода](#выполнение-кода)
10. [Шаблоны](#шаблоны)
11. [Credentials](#credentials)
12. [Отложенные сообщения и Cron](#отложенные-сообщения-и-cron)
13. [Примеры использования](#примеры-использования)

---

## Введение

DBCV - это NoCode/LowCode платформа для создания и управления ботами (агентами) через визуальный конструктор.

### Основные возможности:

- ✅ Создание диалоговых сценариев без программирования
- ✅ Система шагов с условными переходами
- ✅ Выполнение HTTP запросов к внешним API
- ✅ Выполнение Python кода для сложной логики
- ✅ Система переменных (бот, пользователь, сессия, канал)
- ✅ Шаблоны для переиспользования
- ✅ Отложенные сообщения и периодические задачи
- ✅ Интеграция с внешними сервисами (в разработке)

### Архитектура:

- **Backend**: FastAPI + FastStream + PostgreSQL + Redis
- **Обработка сообщений**: Redis Streams с consumer groups
- **Хранилище файлов**: MinIO/S3
- **MCP Server**: AI-ассистент для создания ботов

Подробнее об архитектуре см. [architecture.md](architecture.md)

---

## Быстрый старт

### Установка

```bash
# Клонирование репозитория
git clone <repository-url>
cd DBCV

# Запуск через Docker Compose
docker-compose up -d

# Применение миграций
docker-compose exec backend alembic upgrade head
```

### Первый бот

1. Создайте пользователя через `/api/v1/login/register`
2. Создайте канал через `/api/v1/channels`
3. Создайте бота через `/api/v1/bots`
4. Создайте шаг через `/api/v1/steps`
5. Создайте connection group через `/api/v1/connection_groups`
6. Создайте connection через `/api/v1/connections`

---

## API Endpoints

### Базовый URL

```
http://localhost:8003/api/v1
```

### Аутентификация

Большинство endpoints требуют JWT токен в заголовке:
```
Authorization: Bearer <token>
```

### Основные endpoints

#### Боты
- `GET /bots` - список ботов
- `POST /bots` - создание бота
- `GET /bots/{bot_id}` - получение бота
- `PUT /bots/{bot_id}` - обновление бота
- `DELETE /bots/{bot_id}` - удаление бота

#### Шаги
- `GET /steps` - список шагов
- `POST /steps` - создание шага
- `GET /steps/{step_id}` - получение шага
- `PUT /steps/{step_id}` - обновление шага
- `DELETE /steps/{step_id}` - удаление шага

#### Connection Groups
- `GET /connection_groups` - список групп связей
- `POST /connection_groups` - создание группы связей
- `GET /connection_groups/{group_id}` - получение группы связей
- `PUT /connection_groups/{group_id}` - обновление группы связей
- `DELETE /connection_groups/{group_id}` - удаление группы связей

#### Connections
- `GET /connections` - список связей
- `POST /connections` - создание связи
- `GET /connections/{connection_id}` - получение связи
- `PUT /connections/{connection_id}` - обновление связи
- `DELETE /connections/{connection_id}` - удаление связи

#### HTTP Запросы
- `GET /requests` - список запросов
- `POST /requests` - создание запроса
- `GET /requests/{request_id}` - получение запроса
- `PUT /requests/{request_id}` - обновление запроса
- `DELETE /requests/{request_id}` - удаление запроса
- `POST /requests/{request_id}/execute` - выполнение запроса

#### Сообщения
- `GET /messages` - список сообщений
- `POST /messages` - создание сообщения
- `GET /messages/{message_id}` - получение сообщения

#### Каналы
- `GET /channels` - список каналов
- `POST /channels` - создание канала
- `GET /channels/{channel_id}` - получение канала
- `PUT /channels/{channel_id}` - обновление канала

#### Шаблоны
- `GET /templates` - список шаблонов
- `POST /templates` - создание шаблона
- `GET /templates/{template_id}` - получение шаблона
- `POST /template_instance` - создание экземпляра шаблона

#### Credentials
- `GET /bots/{bot_id}/credentials` - список credentials бота
- `POST /bots/{bot_id}/credentials` - создание credential
- `GET /bots/{bot_id}/credentials/{credential_id}` - получение credential
- `DELETE /bots/{bot_id}/credentials/{credential_id}` - удаление credential

#### Отложенные сообщения
- `GET /emitters` - список emitters
- `POST /emitters` - создание emitter
- `DELETE /emitters/{emitter_id}` - удаление emitter

#### Cron задачи
- `GET /crons` - список cron задач
- `POST /crons` - создание cron задачи
- `DELETE /crons/{cron_id}` - удаление cron задачи

Полный список endpoints доступен в Swagger UI: `http://localhost:8003/docs`

---

## Работа с ботами

### Создание бота

```json
POST /api/v1/bots
{
  "name": "Мой бот",
  "description": "Описание бота",
  "first_step_id": "uuid-шага"
}
```

### Структура бота

Бот состоит из:
- **Шаги** (steps) - узлы диалогового сценария
- **Связи** (connections) - переходы между шагами
- **Переменные** (bot_variables) - данные бота
- **First Step** - начальный шаг при старте

### Выполнение бота

1. Пользователь отправляет сообщение
2. FastStream Worker получает сообщение из Redis Stream
3. Создается/обновляется сессия пользователя с ботом
4. Выполняется текущий шаг из сессии
5. Обрабатываются connection groups
6. Проверяются правила (rules) в connections
7. При выполнении правила - переход на следующий шаг

---

## Система шагов

### Шаг (Step)

Шаг - это узел в диалоговом сценарии бота.

**Поля:**
- `name` - название шага
- `description` - описание
- `is_proxy` - автоматический переход (true) или ожидание сообщения (false)
- `timeout_after` - таймаут в секундах
- `message` - сообщение, отправляемое пользователю
- `connection_groups` - группы связей для переходов

### Типы шагов

#### 1. Обычный шаг (`is_proxy=false`)
- Отправляет сообщение пользователю
- Ожидает ответа пользователя
- При следующем сообщении проверяет rules и переходит дальше

#### 2. Прокси-шаг (`is_proxy=true`)
- Отправляет сообщение (если есть)
- Сразу обрабатывает connection groups
- Автоматически переходит дальше по правилам

### Создание шага

```json
POST /api/v1/steps
{
  "bot_id": "uuid-бота",
  "name": "Приветствие",
  "description": "Шаг приветствия",
  "is_proxy": false,
  "timeout_after": 60
}
```

---

## Система переменных

### Scopes (области видимости)

Переменные доступны в формате `{scope}.{key}`:

- `bot.*` - переменные бота
- `user.*` - переменные пользователя
- `session.*` - переменные сессии
- `channel.*` - переменные канала
- `message.*` - данные текущего сообщения

### Использование переменных

#### В текстах сообщений:
```
"Hello {$user.name$}! Your score is {$session.score$}"
```

#### В правилах (rules):
```json
{
  "field": "message.text",
  "operator": "equals",
  "value": "{$bot.start_command$}"
}
```

#### В HTTP запросах:
- URL: `https://api.example.com/users/{$user.id$}`
- Headers: `{"Authorization": "Bearer {$bot.api_token$}"}`
- Body: `{"userId": "{$user.id$}", "score": {$session.score$}}`

#### В Python коде:
```python
async def main(message: dict | None, variables: dict):
    user_name = variables.get("user", {}).get("name")
    bot_token = variables.get("bot", {}).get("api_token")
    session_score = variables.get("session", {}).get("score")
    return {"result": f"User {user_name} has score {session_score}"}
```

### Сохранение переменных

В connection group можно указать `variables` для сохранения результатов:

```json
{
  "variables": {
    "session.score": "response.result.score",
    "user.last_action": "response.result.action"
  }
}
```

---

## Правила (Rules)

Правила используются для условных переходов между шагами.

### Формат правила

```json
{
  "condition": "AND",
  "rules": [
    {
      "field": "message.text",
      "operator": "equals",
      "value": "start"
    },
    {
      "field": "user.score",
      "operator": "greater_than",
      "value": 100
    }
  ]
}
```

### Операторы

- `equals` - равно
- `not_equals` - не равно
- `contains` - содержит
- `not_contains` - не содержит
- `greater_than` - больше
- `less_than` - меньше
- `greater_than_or_equal` - больше или равно
- `less_than_or_equal` - меньше или равно
- `in` - входит в список
- `not_in` - не входит в список
- `is_empty` - пусто
- `is_not_empty` - не пусто

### Условия

- `AND` - все правила должны быть выполнены
- `OR` - хотя бы одно правило должно быть выполнено

### Примеры правил

#### Проверка текста сообщения:
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

#### Проверка числового значения:
```json
{
  "condition": "AND",
  "rules": [
    {
      "field": "session.score",
      "operator": "greater_than",
      "value": 100
    }
  ]
}
```

#### Проверка в списке:
```json
{
  "condition": "AND",
  "rules": [
    {
      "field": "message.text",
      "operator": "in",
      "value": ["yes", "y", "да", "ок"]
    }
  ]
}
```

#### IF/ELSE через priority:

**IF connection (priority=0):**
```json
{
  "next_step_id": "uuid-if-step",
  "rules": {
    "condition": "AND",
    "rules": [{"field": "message.text", "operator": "equals", "value": "start"}]
  },
  "priority": 0
}
```

**ELSE connection (priority=1):**
```json
{
  "next_step_id": "uuid-else-step",
  "rules": {},
  "priority": 1
}
```

Пустое правило `{}` всегда True, поэтому это ELSE case.

---

## HTTP запросы

### Создание запроса

```json
POST /api/v1/requests
{
  "name": "Get User Data",
  "method": "GET",
  "request_url": "https://api.example.com/users/{$user.id$}",
  "headers": "{\"Authorization\": \"Bearer {$bot.api_token$}\"}",
  "params": "{\"include\": \"profile\"}"
}
```

### Поля запроса

- `method` - HTTP метод (GET, POST, PUT, DELETE и т.д.)
- `request_url` - URL с подстановкой переменных
- `headers` - заголовки (JSON строка)
- `params` - query параметры (JSON строка)
- `json_field` - JSON body (JSON строка)
- `data` - form-data (JSON строка)
- `attachments` - файлы (массив ID attachments)
- `proxies` - прокси (JSON строка)

### Выполнение запроса

#### Через Connection Group:

1. Создайте Request
2. Создайте Connection Group с `search_type="response"` и `request_id`
3. При выполнении шага запрос выполнится автоматически

#### Через API:

```json
POST /api/v1/requests/{request_id}/execute
{
  "bot_id": "uuid-бота",
  "variables": {
    "user": {"id": "123"},
    "bot": {"api_token": "token123"}
  },
  "dry_run": false
}
```

### Подстановка переменных

Все поля запроса поддерживают подстановку переменных:
- URL: `https://api.example.com/users/{$user.id$}`
- Headers: `{"Authorization": "Bearer {$bot.token$}"}`
- Body: `{"userId": "{$user.id$}", "score": {$session.score$}}`

---

## Выполнение кода

### Правила написания кода

Поле `code` в Connection Group должно содержать асинхронную функцию `main`:

```python
async def main(message: dict | None, variables: dict):
    # Ваш код здесь
    return {"result": "value"}
```

### Параметры

- `message` - текущее сообщение (может быть `None`)
- `variables` - словарь с переменными:
  ```python
  {
    "bot": {...},      # переменные бота
    "session": {...},  # переменные сессии
    "user": {...},     # переменные пользователя
    "channel": {...}   # переменные канала
  }
  ```

### Доступные функции

**Базовые типы:**
- `int, str, float, bool, bytes, list, tuple, dict`

**Встроенные функции:**
- `len, range, enumerate, zip, isinstance, type`
- `max, min, abs, round, sum, sorted, reversed`

**Математические:**
- `ceil, floor, trunc, sqrt, log, log10, log2, pow, exp`
- `sin, cos, tan, asin, acos, atan`
- `radians, degrees, fabs, fmod`

**Работа с данными:**
- `json.loads, json.dumps` - работа с JSON
- `datetime, timedelta` - работа с датами
- `re.match, re.search, re.findall, re.sub` - регулярные выражения
- `random.randint, random.choice` - случайные числа

**Итераторы:**
- `product, permutations, combinations` - комбинаторика
- `accumulate, groupby, chain, count, cycle, repeat`

**Статистика:**
- `statistics.mean, statistics.median, statistics.stdev`

**UUID:**
- `uuid4` - генерация UUID

### Примеры кода

#### Простая обработка:
```python
async def main(message: dict | None, variables: dict):
    if message:
        text = message.get("text", "")
        return {"processed_text": text.upper()}
    return {}
```

#### Работа с переменными:
```python
async def main(message: dict | None, variables: dict):
    user_name = variables.get("user", {}).get("name", "Guest")
    session_score = variables.get("session", {}).get("score", 0)
    
    new_score = session_score + 10
    
    return {
        "user_name": user_name,
        "new_score": new_score,
        "message": f"Hello {user_name}, your score is {new_score}"
    }
```

#### Обработка JSON:
```python
async def main(message: dict | None, variables: dict):
    import json
    
    if message:
        params = message.get("params", {})
        if isinstance(params, str):
            params = json.loads(params)
        
        data = {
            "processed": True,
            "params": params
        }
        
        return {"result": json.dumps(data)}
    
    return {}
```

#### Работа с датами:
```python
async def main(message: dict | None, variables: dict):
    from datetime import datetime, timedelta
    
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    
    return {
        "current_time": now.isoformat(),
        "tomorrow": tomorrow.isoformat()
    }
```

### Ограничения

- ❌ Нет доступа к файловой системе
- ❌ Нет прямого доступа к сети (используйте Request)
- ❌ Нет доступа к системным командам
- ❌ Ограниченный набор функций (безопасность)

---

## Шаблоны

Шаблоны позволяют переиспользовать структуры шагов.

### Создание шаблона

```json
POST /api/v1/templates
{
  "name": "API Request Template",
  "description": "Шаблон для API запроса",
  "inputs": {
    "type": "object",
    "properties": {
      "api_url": {"type": "string"},
      "api_key": {"type": "string"}
    },
    "required": ["api_url", "api_key"]
  },
  "outputs": {
    "type": "object",
    "properties": {
      "result": {"type": "object"}
    }
  },
  "steps": [...]
}
```

### Создание экземпляра шаблона

```json
POST /api/v1/template_instance
{
  "template_id": "uuid-шаблона",
  "bot_id": "uuid-бота",
  "inputs_mapping": {
    "api_url": "{$bot.api_url$}",
    "api_key": "{$bot.api_key$}"
  },
  "outputs_mapping": {
    "result": "session.api_result"
  }
}
```

При создании экземпляра создается прокси-шаг, который при выполнении заменяется на шаги шаблона.

---

## Credentials

Credentials используются для безопасного хранения токенов и ключей API.

### Создание credential

```json
POST /api/v1/bots/{bot_id}/credentials
{
  "provider": "telegram",
  "strategy": "api_key",
  "data": {
    "bot_token": "123456:ABC-DEF..."
  }
}
```

### Providers

- `telegram` - Telegram Bot API
- `google` - Google Services (OAuth)
- `openai` - OpenAI API
- И другие

### Strategies

- `api_key` - простой API ключ
- `oauth` - OAuth токены

### Использование в коде

Credentials автоматически получаются через `CredentialsResolver` при выполнении интеграций (в разработке).

---

## Отложенные сообщения и Cron

### Emitter (Отложенное сообщение)

Создание отложенного сообщения:

```json
POST /api/v1/emitters
{
  "bot_id": "uuid-бота",
  "message_id": "uuid-сообщения",
  "scheduled_at": "2024-01-01T12:00:00Z"
}
```

Сообщение будет отправлено в указанное время.

### Cron (Периодические задачи)

Создание cron задачи:

```json
POST /api/v1/crons
{
  "name": "Daily Report",
  "cron_expression": "0 9 * * *",
  "bot_id": "uuid-бота",
  "message_id": "uuid-сообщения"
}
```

### Cron выражения

Формат: `минута час день месяц день_недели`

**Примеры:**
- `0 9 * * *` - каждый день в 9:00
- `*/5 * * * *` - каждые 5 минут
- `0 0 1 * *` - первого числа каждого месяца
- `0 9 * * 1` - каждый понедельник в 9:00

**Специальные значения:**
- `*` - любое значение
- `*/a` - каждые a значений
- `a-b` - диапазон от a до b
- `a-b/c` - каждые c значений в диапазоне a-b
- `xth y` - x-е вхождение дня недели y в месяце
- `last x` - последнее вхождение дня недели x
- `last` - последний день месяца
- `x,y,z` - несколько значений

Подробнее: https://apscheduler.readthedocs.io/en/3.x/modules/triggers/cron.html

---

## Примеры использования

### Пример 1: Простой бот с приветствием

1. **Создайте бота:**
```json
POST /api/v1/bots
{
  "name": "Greeting Bot",
  "description": "Бот приветствия"
}
```

2. **Создайте шаг:**
```json
POST /api/v1/steps
{
  "bot_id": "uuid-бота",
  "name": "Start",
  "is_proxy": true
}
```

3. **Создайте сообщение для шага:**
```json
POST /api/v1/messages
{
  "step_id": "uuid-шага",
  "text": "Hello! Welcome to our bot!"
}
```

4. **Создайте connection group:**
```json
POST /api/v1/connection_groups
{
  "step_id": "uuid-шага",
  "search_type": "message"
}
```

5. **Установите first_step бота:**
```json
PUT /api/v1/bots/{bot_id}
{
  "first_step_id": "uuid-шага"
}
```

### Пример 2: Бот с условием

1. **Создайте шаг "Check Command":**
```json
POST /api/v1/steps
{
  "bot_id": "uuid-бота",
  "name": "Check Command",
  "is_proxy": true
}
```

2. **Создайте connection group:**
```json
POST /api/v1/connection_groups
{
  "step_id": "uuid-шага",
  "search_type": "message"
}
```

3. **Создайте IF connection:**
```json
POST /api/v1/connections
{
  "group_id": "uuid-группы",
  "next_step_id": "uuid-шага-start",
  "rules": {
    "condition": "AND",
    "rules": [
      {
        "field": "message.text",
        "operator": "equals",
        "value": "start"
      }
    ]
  },
  "priority": 0
}
```

4. **Создайте ELSE connection:**
```json
POST /api/v1/connections
{
  "group_id": "uuid-группы",
  "next_step_id": "uuid-шага-help",
  "rules": {},
  "priority": 1
}
```

### Пример 3: Бот с API запросом

1. **Создайте Request:**
```json
POST /api/v1/requests
{
  "name": "Get User Info",
  "method": "GET",
  "request_url": "https://api.example.com/users/{$user.id$}",
  "headers": "{\"Authorization\": \"Bearer {$bot.api_token$}\"}"
}
```

2. **Создайте Connection Group с запросом:**
```json
POST /api/v1/connection_groups
{
  "step_id": "uuid-шага",
  "search_type": "response",
  "request_id": "uuid-запроса",
  "variables": {
    "session.user_info": "response.result"
  }
}
```

3. **Создайте Connection:**
```json
POST /api/v1/connections
{
  "group_id": "uuid-группы",
  "next_step_id": "uuid-следующего-шага",
  "rules": {},
  "priority": 0
}
```

### Пример 4: Бот с кодом

1. **Создайте Connection Group с кодом:**
```json
POST /api/v1/connection_groups
{
  "step_id": "uuid-шага",
  "search_type": "code",
  "code": "async def main(message: dict | None, variables: dict):\n    user_name = variables.get('user', {}).get('name', 'Guest')\n    return {'greeting': f'Hello, {user_name}!'}",
  "variables": {
    "session.greeting": "greeting"
  }
}
```

---

## Дополнительные ресурсы

- [architecture.md](architecture.md) - подробная архитектура системы
- [Student Tasks.md](STUDENT_TASKS.md) - задачи для студентов
- Swagger UI: `http://localhost:8003/docs`
- Admin Panel: `http://localhost:8003/admin`

---

## Поддержка

При возникновении вопросов:
1. Проверьте документацию
2. Изучите примеры в Swagger UI
3. Обратитесь к команде разработки