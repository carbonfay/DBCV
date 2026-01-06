# Примеры промптов для нейросетей при реализации интеграций

## ⚠️ Важное предупреждение (Дисклеймер)

**Мы начинаем трек выполнения практического задания.**

Вам будет дана возможность использовать **вайбкодинг** (AI-ассистированное программирование) и **ИИ-инструменты** для участия в разработке сложной платформы. Конкретно вы получите задания по реализации интеграций.

**Что это значит простыми словами:**

- 🎯 **Вы будете работать с AI** - это нормально и даже приветствуется!
- 🤖 **AI будет писать код за вас** - вы будете давать ему задания (промпты), а он будет генерировать код.
- 📚 **Вы будете учиться** - даже если AI пишет код, вы должны понимать, что он делает.
- ✅ **Ваша задача** - правильно формулировать запросы к AI, проверять код, тестировать и исправлять ошибки.

**Это не значит, что вы "обманываете"** - это современный подход к разработке!

**Если вы не понимаете что-то** - это нормально! Читайте документацию, задавайте вопросы, изучайте примеры.

---

## Общая концепция

**Что такое промпт?** Промпт - это запрос к AI на русском языке, который объясняет, что нужно сделать.

**Как использовать этот документ:**
1. Найдите промпт для вашей интеграции
2. Скопируйте его
3. Вставьте в AI-инструмент (Cursor, ChatGPT, Claude и т.д.)
4. Получите код от AI
5. Проверьте и исправьте код при необходимости

**Какие AI-инструменты можно использовать:**
- ✅ **Cursor** (рекомендуется) - https://cursor.sh
- ✅ **Codex** - расширение ChatGPT для VS Code
- ✅ **ChatGPT** - https://chat.openai.com (браузер или CLI)
- ✅ **Claude** - https://claude.ai (браузер или CLI)
- ✅ **GitHub Copilot** - расширение для VS Code (есть бесплатный)
- ✅ **Codeium** - альтернатива Copilot
- ✅ **Любые другие** AI-инструменты для программирования

Этот документ содержит примеры промптов, которые студенты могут использовать при работе с нейросетями (ChatGPT, Claude, Copilot и др.) для реализации интеграций в платформе DBCV.

## Базовый промпт-шаблон

```
Ты помогаешь реализовать интеграцию для платформы DBCV.

КОНТЕКСТ:
- Платформа DBCV - это NoCode/LowCode система для создания ботов
- Интеграции используют готовые библиотеки внутри backend кода
- Все интеграции наследуются от BaseIntegration
- Credentials получаются через CredentialsResolver

ЗАДАЧА:
Реализовать интеграцию: {НАЗВАНИЕ_ИНТЕГРАЦИИ}

ТРЕБОВАНИЯ:
1. Создать класс {Service}{Action}Integration, наследующий BaseIntegration
2. Использовать библиотеку {БИБЛИОТЕКА} версии {ВЕРСИЯ}
3. Метод execute() должен:
   - Получать credentials через credentials_resolver.get_default_for()
   - Использовать библиотеку напрямую (не через HTTP запросы)
   - Обрабатывать ошибки библиотеки
   - Возвращать результат в формате {"response": {"ok": True, "result": {...}}}
4. Метаданные должны включать:
   - id: "{service}_{action}"
   - version: "1.0.0"
   - category: "{category}"
   - icon_s3_key: "icons/integrations/{service}.svg"
   - config_schema: JSON Schema для параметров
   - credentials_provider: "{service}"
   - credentials_strategy: "api_key" или "oauth"
   - library_name: "{library}"
5. Добавить примеры использования в examples

ПРИМЕРЫ:
- См. backend/app/integrations/telegram/send_message.py
- См. backend/app/integrations/README.md
- См. backend/app/integrations/SAFE_LIBRARIES.md

БИБЛИОТЕКА:
{ОПИСАНИЕ_БИБЛИОТЕКИ_И_ЕЕ_ИСПОЛЬЗОВАНИЯ}

КОНФИГУРАЦИЯ:
Параметры интеграции:
{СПИСОК_ПАРАМЕТРОВ_С_ОПИСАНИЕМ}

РЕЗУЛЬТАТ:
Создай файл backend/app/integrations/{service}/{action}.py с полной реализацией.
```

---

## Примеры конкретных промптов

### 1. Telegram Get Updates

```
Реализовать интеграцию: Telegram Get Updates

БИБЛИОТЕКА: python-telegram-bot>=20.0
ИСПОЛЬЗОВАНИЕ: 
from telegram import Bot
from telegram.error import TelegramError

bot = Bot(token=creds["bot_token"])
updates = await bot.get_updates(offset=offset, limit=limit)

ПАРАМЕТРЫ:
- offset (int, optional): Offset для получения обновлений (по умолчанию 0)
- limit (int, optional): Максимальное количество обновлений (1-100, по умолчанию 100)

CREDENTIALS:
- provider: "telegram"
- strategy: "api_key"
- поле в payload: "bot_token"

РЕЗУЛЬТАТ:
Возвращать список обновлений в формате:
{
  "response": {
    "ok": True,
    "result": {
      "updates": [...],
      "count": 10
    }
  }
}

ОБРАБОТКА ОШИБОК:
- Обработать TelegramError
- Вернуть {"response": {"ok": False, "error_code": 400, "description": "..."}}
```

### 2. Telegram Send Photo

```
Реализовать интеграцию: Telegram Send Photo

БИБЛИОТЕКА: python-telegram-bot>=20.0
ИСПОЛЬЗОВАНИЕ:
from telegram import Bot
from telegram.error import TelegramError

bot = Bot(token=creds["bot_token"])
message = await bot.send_photo(
    chat_id=chat_id,
    photo=photo,  # может быть file_id, URL или file object
    caption=caption,
    parse_mode=parse_mode
)

ПАРАМЕТРЫ:
- chat_id (string, required): ID чата или пользователя
- photo (string, required): file_id, URL или путь к файлу
- caption (string, optional): Подпись к фото
- parse_mode (string, optional): "HTML", "Markdown" или "MarkdownV2"

CREDENTIALS:
- provider: "telegram"
- strategy: "api_key"
- поле в payload: "bot_token"

РЕЗУЛЬТАТ:
{
  "response": {
    "ok": True,
    "result": {
      "message_id": 123,
      "chat": {...},
      "photo": [...]
    }
  }
}
```

### 3. OpenAI Chat Completion

```
Реализовать интеграцию: OpenAI Chat Completion

БИБЛИОТЕКА: openai>=1.0.0
ИСПОЛЬЗОВАНИЕ:
from openai import OpenAI
from openai import OpenAIError

client = OpenAI(api_key=creds["api_key"])
response = await client.chat.completions.create(
    model=model,
    messages=messages,
    temperature=temperature,
    max_tokens=max_tokens
)

ПАРАМЕТРЫ:
- model (string, required): ID модели (например, "gpt-4", "gpt-3.5-turbo")
- messages (array, required): Массив сообщений в формате [{"role": "user", "content": "..."}]
- temperature (float, optional): Температура (0-2, по умолчанию 1)
- max_tokens (int, optional): Максимальное количество токенов

CREDENTIALS:
- provider: "openai"
- strategy: "api_key"
- поле в payload: "api_key"

РЕЗУЛЬТАТ:
{
  "response": {
    "ok": True,
    "result": {
      "choices": [...],
      "usage": {...}
    }
  }
}
```

### 4. Discord Send Message

```
Реализовать интеграцию: Discord Send Message

БИБЛИОТЕКА: discord.py>=2.3.0
ИСПОЛЬЗОВАНИЕ:
import discord
from discord import Webhook

webhook = Webhook.from_url(webhook_url, client=discord.Client())
await webhook.send(content=content, username=username)

ПАРАМЕТРЫ:
- webhook_url (string, required): URL Discord webhook
- content (string, required): Текст сообщения
- username (string, optional): Имя пользователя для webhook

CREDENTIALS:
- provider: "discord"
- strategy: "api_key"
- поле в payload: "webhook_url"

РЕЗУЛЬТАТ:
{
  "response": {
    "ok": True,
    "result": {
      "id": "...",
      "content": "..."
    }
  }
}
```

### 5. Google Sheets Read (через httpx)

```
Реализовать интеграцию: Google Sheets Read

БИБЛИОТЕКА: httpx (для прямых HTTP запросов к Google Sheets API)
ИСПОЛЬЗОВАНИЕ:
import httpx

async with httpx.AsyncClient() as client:
    response = await client.get(
        f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

ПАРАМЕТРЫ:
- spreadsheet_id (string, required): ID таблицы Google Sheets
- range (string, required): Диапазон ячеек (например, "Sheet1!A1:B10")
- access_token (string, required): OAuth токен доступа

CREDENTIALS:
- provider: "google"
- strategy: "oauth"
- поле в payload: "access_token"

РЕЗУЛЬТАТ:
{
  "response": {
    "ok": True,
    "result": {
      "values": [[...], [...]],
      "range": "..."
    }
  }
}
```

### 6. Stripe Create Payment

```
Реализовать интеграцию: Stripe Create Payment

БИБЛИОТЕКА: stripe>=7.0.0
ИСПОЛЬЗОВАНИЕ:
import stripe
from stripe.error import StripeError

stripe.api_key = creds["api_key"]
payment_intent = stripe.PaymentIntent.create(
    amount=amount,
    currency=currency,
    payment_method=payment_method_id
)

ПАРАМЕТРЫ:
- amount (int, required): Сумма в центах (например, 1000 = $10.00)
- currency (string, required): Валюта (например, "usd", "rub")
- payment_method_id (string, optional): ID метода оплаты
- description (string, optional): Описание платежа

CREDENTIALS:
- provider: "stripe"
- strategy: "api_key"
- поле в payload: "api_key"

РЕЗУЛЬТАТ:
{
  "response": {
    "ok": True,
    "result": {
      "id": "pi_...",
      "status": "succeeded",
      "amount": 1000
    }
  }
}
```

### 7. AmoCRM Create Contact (через httpx)

```
Реализовать интеграцию: AmoCRM Create Contact

БИБЛИОТЕКА: httpx (для прямых HTTP запросов к AmoCRM API)
ИСПОЛЬЗОВАНИЕ:
import httpx

async with httpx.AsyncClient() as client:
    # Сначала получить access_token через OAuth
    token_response = await client.post(
        "https://{subdomain}.amocrm.ru/oauth2/access_token",
        json={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri
        }
    )
    
    # Затем создать контакт
    response = await client.post(
        f"https://{subdomain}.amocrm.ru/api/v4/contacts",
        headers={"Authorization": f"Bearer {access_token}"},
        json=[{
            "name": name,
            "custom_fields_values": custom_fields
        }]
    )

ПАРАМЕТРЫ:
- subdomain (string, required): Поддомен AmoCRM
- name (string, required): Имя контакта
- custom_fields (array, optional): Дополнительные поля

CREDENTIALS:
- provider: "amocrm"
- strategy: "oauth"
- поля в payload: "client_id", "client_secret", "access_token", "refresh_token"

РЕЗУЛЬТАТ:
{
  "response": {
    "ok": True,
    "result": {
      "id": 12345,
      "name": "..."
    }
  }
}
```

### 8. Yandex Translate Text (через httpx)

```
Реализовать интеграцию: Yandex Translate Text

БИБЛИОТЕКА: httpx (для прямых HTTP запросов к Yandex Translate API)
ИСПОЛЬЗОВАНИЕ:
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "https://translate.yandex.net/api/v1.5/tr.json/translate",
        params={
            "key": api_key,
            "text": text,
            "lang": lang
        }
    )

ПАРАМЕТРЫ:
- text (string, required): Текст для перевода
- lang (string, required): Направление перевода (например, "en-ru", "ru-en")
- api_key (string, required): API ключ Yandex Translate

CREDENTIALS:
- provider: "yandex_cloud"
- strategy: "api_key"
- поле в payload: "api_key"

РЕЗУЛЬТАТ:
{
  "response": {
    "ok": True,
    "result": {
      "text": ["Переведенный текст"],
      "lang": "en-ru"
    }
  }
}
```

---

## Советы по использованию промптов

### 1. Адаптация под конкретную задачу

- Замените `{НАЗВАНИЕ_ИНТЕГРАЦИИ}` на конкретное название
- Укажите точную версию библиотеки из `SAFE_LIBRARIES.md`
- Добавьте все необходимые параметры с описанием

### 2. Проверка результата

После получения кода от нейросети:

1. Проверьте, что класс наследуется от `BaseIntegration`
2. Убедитесь, что используется правильная библиотека
3. Проверьте обработку ошибок
4. Убедитесь, что формат возвращаемых данных соответствует требованиям
5. Проверьте, что все метаданные заполнены

### 3. Итеративное улучшение

Если код не идеален:

1. Попросите нейросеть исправить конкретные ошибки
2. Укажите на пример из `telegram/send_message.py`
3. Попросите добавить недостающие части (обработка ошибок, валидация и т.д.)

### 4. Использование контекста

Добавьте в промпт:

```
КОНТЕКСТ ПРОЕКТА:
- Структура проекта: backend/app/integrations/{service}/{action}.py
- Пример существующей интеграции: backend/app/integrations/telegram/send_message.py
- Базовый класс: backend/app/integrations/base.py
- Реестр: backend/app/integrations/registry.py
```

---

## Частые ошибки и как их избежать

### Ошибка 1: Неправильное получение credentials

**Неправильно:**
```python
creds = credentials_resolver.get_default_for(...)  # синхронный вызов
```

**Правильно:**
```python
creds = await credentials_resolver.get_default_for(...)  # асинхронный вызов
```

### Ошибка 2: Неправильный формат возврата

**Неправильно:**
```python
return {"ok": True, "result": {...}}
```

**Правильно:**
```python
return {"response": {"ok": True, "result": {...}}}
```

### Ошибка 3: Отсутствие обработки ошибок

**Неправильно:**
```python
result = await client.method()
return {"response": {"ok": True, "result": result}}
```

**Правильно:**
```python
try:
    result = await client.method()
    return {"response": {"ok": True, "result": result}}
except LibraryError as e:
    await logger.error(f"Error: {e}")
    return {"response": {"ok": False, "error_code": 500, "description": str(e)}}
```

---

## Дополнительные ресурсы

- [Документация по интеграциям](../backend/app/integrations/README.md)
- [Список безопасных библиотек](../backend/app/integrations/SAFE_LIBRARIES.md)
- [Пример интеграции Telegram](../backend/app/integrations/telegram/send_message.py)
- [Базовый класс интеграций](../backend/app/integrations/base.py)

---

**Удачи в реализации!**

