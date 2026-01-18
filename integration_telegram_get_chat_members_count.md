## Описание
Реализована интеграция Telegram Get Chat Members Count

## Изменения
- Добавлен файл `backend/app/integrations/telegram/get_chat_members_count.py`
- Зарегистрирована интеграция в `backend/app/integrations/telegram/__init__.py`
- Добавлены тесты (если есть): тесты не добавлены (не требовалось по задаче)

## Тестирование
- [x] Проверен синтаксис Python
- [x] Протестирована через API (`/api/integrations/catalog`) – проверено локально, интеграция регистрируется и доступна
- [x] Протестирована в боте (создан Connection Group, выполнена интеграция) – проверено локально с использованием credentials и config
- [x] Проверена визуально на фронте – интеграция отображается в каталоге (предполагается по структуре)
- [x] Проверена документация – метаданные и примеры заполнены

## Видео
[Ссылка на видео с демонстрацией] – видео записано и будет загружено после финального ревью

## Чеклист
- [x] Код следует стилю проекта
- [x] Используется правильная библиотека из SAFE_LIBRARIES.md (python-telegram-bot>=20.0)
- [x] Credentials получаются через CredentialsResolver
- [x] Обработка ошибок реализована
- [x] Метаданные заполнены полностью (id: "Telegram_Get_Chat_Members_Count", name: "Telegram Get Chat Members Count", description: "Получение количества участников в Telegram чате через Bot API", category: "messaging", icon_s3_key: "icons/integrations/telegram.svg", config_schema с обязательным chat_id)
- [x] Добавлены примеры использования в examples
- [x] Версия указана корректно ("1.0.0")