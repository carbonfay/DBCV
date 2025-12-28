# PR: Telegram Get Chat Members Count Integration

## Описание
Реализована интеграция Telegram Get Chat Members Count для получения количества участников (подписчиков) в Telegram чате, группе или канале.

## Изменения
- Добавлен файл `backend/app/integrations/telegram/get_chat_members_count.py`
- Зарегистрирована интеграция в `backend/app/integrations/telegram/__init__.py`
- Использована библиотека `python-telegram-bot` для работы с Telegram Bot API

## Функциональность
- Получение количества участников по chat_id
- Поддержка публичных каналов (через @username)
- Поддержка приватных групп и супергрупп (через числовой ID)
- Получение дополнительной информации о чате (тип, название, username)
- Обработка всех типов ошибок Telegram API (InvalidToken, BadRequest, Forbidden, TelegramError)

## Тестирование
- [x] Проверен синтаксис Python
- [x] Устранены синтаксические ошибки (удалены markdown символы ```)
- [x] Пересобран Docker образ backend
- [x] Backend контейнер успешно запущен без ошибок
- [x] Интеграция успешно импортируется и создается
- [x] Метаданные корректно возвращаются
- [ ] Протестирована через API (`/api/v1/integrations/catalog`)
- [ ] Протестирована в боте (создан Connection Group, выполнена интеграция)
- [ ] Проверена визуально на фронте

## Результаты тестирования
```
============================================================
Telegram Get Chat Members Count Integration
============================================================
ID: telegram_get_chat_members_count
Version: 1.0.0
Name: Telegram Get Chat Members Count
Description: Получение количества участников (подписчиков) в Telegram чате, группе или канале
Category: messaging
Credentials Provider: telegram
Library: python-telegram-bot
Examples count: 3
============================================================
✅ Integration works successfully!
============================================================
```

## Примеры использования

### 1. Получить количество подписчиков публичного канала
```json
{
  "chat_id": "@channelname"
}
```

### 2. Получить количество участников приватной группы
```json
{
  "chat_id": "-1001234567890"
}
```

### 3. Получить количество участников супергруппы
```json
{
  "chat_id": "-100987654321"
}
```

## Формат ответа
```json
{
  "response": {
    "ok": true,
    "result": {
      "chat_id": "@channelname",
      "member_count": 1234,
      "chat": {
        "id": -1001234567890,
        "type": "channel",
        "title": "My Channel",
        "username": "channelname"
      }
    }
  }
}
```

## Обработка ошибок
- **InvalidToken (401)**: Неверный bot token
- **BadRequest (400)**: Неверный chat_id или чат не найден
- **Forbidden (403)**: Бот заблокирован или не имеет доступа к чату
- **TelegramError (500)**: Общие ошибки Telegram API
- **Exception (500)**: Непредвиденные ошибки

## Чеклист
- [x] Код следует стилю проекта
- [x] Используется правильная библиотека из SAFE_LIBRARIES.md (`python-telegram-bot`)
- [x] Credentials получаются через CredentialsResolver
- [x] Обработка ошибок реализована (все типы ошибок Telegram API)
- [x] Метаданные заполнены полностью (id, name, description, category, icon_s3_key, config_schema)
- [x] Добавлены примеры использования в examples (3 примера)
- [x] Версия указана корректно ("1.0.0")
- [x] Исправлены синтаксические ошибки
- [x] Docker образ пересобран
- [x] Backend успешно запущен

## Требования к credentials
```json
{
  "provider": "telegram",
  "strategy": "api_key",
  "payload": {
    "bot_token": "YOUR_BOT_TOKEN"
  }
}
```

## API документация
https://core.telegram.org/bots/api#getchatmembercount

## Видео
[Ссылка на видео с демонстрацией будет добавлена]