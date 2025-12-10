<!-- Copilot / AI agent instructions for working in this repository -->

# Быстрая памятка для AI-кодера (DBCV)

Коротко — что важно знать, чтобы быстро быть продуктивным в этом репозитории.

- **Главная идея проекта**: backend реализует NoCode/LowCode платформу для создания ботов — интеграции с внешними сервисами выполняются внутри backend через готовые библиотеки (не через внешние HTTP-прокси).

- **Ключевые директории**:
  - `backend/app/integrations/` — все интеграции; см. `base.py`, `registry.py`, `SAFE_LIBRARIES.md` и примеры в подпапках (например `telegram/send_message.py`).
  - `backend/app/` — основная логика сервера (engine, auth, managers, loggers и т.д.).
  - `backend/app/tests/integrations/` — тесты для интеграций.

- **Где смотреть шаблон интеграции**: `backend/app/integrations/README.md` содержит пример и рекомендации (включая требование использовать официальные библиотеки из `SAFE_LIBRARIES.md`).

- **Базовый класс интеграций**: `backend/app/integrations/base.py`
  - `IntegrationMetadata` — поля, которые обязательно заполнять (`id`, `version`, `category`, `icon_s3_key`, `config_schema`, `credentials_provider`, `credentials_strategy`, `library_name`, `examples`).
  - `BaseIntegration.execute(self, config, credentials_resolver, bot_id, logger)` — асинхронный метод, который надо реализовать.

- **Как интеграции получают credentials**: всегда через `CredentialsResolver` — см. `app/auth/credentials_resolver.py` и примеры использования (в README и тестах). Ожидаемый вызов: `await credentials_resolver.get_default_for(bot_id=bot_id, provider="<service>", strategy="api_key")`.

- **Требования к реализации интеграции** (явные проектные правила):
  - Импортируйте и используйте библиотеку напрямую внутри файла интеграции (не делать внешние HTTP-прокси).
  - Обрабатывать ошибки библиотеки и возвращать результат в формате:
    ```json
    {"response": {"ok": true, "result": {...}}}
    ```
    или при ошибке
    ```json
    {"response": {"ok": false, "error_code": 400, "description": "..."}}
    ```
  - Метаданные `IntegrationMetadata.id` должны быть в формате `"{service}_{action}"` (например `telegram_send_message`).

- **Регистрация интеграции**:
  - В `backend/app/integrations/{service}/__init__.py` импортируйте класс и зарегистрируйте через `registry.register(MyIntegration())`.
  - В `backend/app/integrations/__init__.py` есть автозагрузка — добавляйте импорт в подпапку `{service}` чтобы он подхватился.

- **Запуск тестов и быстрая верификация**:
  - Тесты для интеграций лежат в `backend/app/tests/integrations/`.
  - Запуск тестов (из корня репозитория):
    ```powershell
    cd backend; pytest -q backend/app/tests/integrations
    ```
  - Репозиторий использует `black`, `mypy`, `isort` — конфиг в `backend/pyproject.toml`.

- **SAFE_LIBRARIES и политика зависимостей**:
  - Перед добавлением новой сторонней библиотеки проверьте `backend/app/integrations/SAFE_LIBRARIES.md` — только безопасные/разрешённые библиотеки.
  - Если библиотека новая, попросите ревью владельца на её добавление и обновление `requirements`/`pyproject.toml`.

- **Примеры кода/шаблоны** (используй как источник копирования):
  - `backend/app/integrations/telegram/send_message.py` — полный рабочий пример интеграции: показывает metadata, получение credentials и формат ответа.
  - `backend/app/integrations/README.md` — шаблон файла интеграции и рекомендации по `config_schema` и `examples`.

- **Нюансы и типичные ловушки**:
  - Всегда делать `await credentials_resolver.get_default_for(...)` и проверять `if not creds: return {"response": {"ok": False, ...}}`.
  - Подстановка переменных из Connection Group выполняется до вызова интеграции (см. `engine/integration_handler.py`), но интеграция должна валидировать `config` в соответствии с `config_schema`.
  - Логирование: используйте предоставленный `logger` (тип `BotLogger`) для ошибок и ключевых шагов.

---

Если какие-то части файла неполные или ты хочешь, чтобы я встроил конкретный пример интеграции (например: сервис, библиотека и параметры), пришли: сервис, действие, библиотеку с версией и схему конфигурации — я автоматически сгенерирую файл интеграции и тест-пример.
