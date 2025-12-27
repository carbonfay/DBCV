# Мок-тесты для Moodle Get Course интеграции

## Описание

Мок-тесты для проверки работы интеграции `MoodleGetCourseIntegration` без реальных HTTP запросов к Moodle API.

## Структура тестов

### Файлы:
- `test_get_course.py` - основные тесты интеграции
- `conftest.py` - конфигурация pytest
- `__init__.py` - инициализация пакета

## Запуск тестов

### Вариант 1: С опцией --noconftest (рекомендуется)
```bash
cd backend
python -m pytest app/tests/integrations/moodle/mock/test_get_course.py -v --noconftest
```

### Вариант 2: Через скрипт
```bash
cd backend
python app/tests/integrations/moodle/mock/run_tests.py
```

## Покрытие тестами

Всего тестов: **15**

### ✅ Успешные сценарии:
1. `test_moodle_metadata` - проверка метаданных интеграции
2. `test_moodle_execute_success_by_id` - получение курса по ID
3. `test_moodle_execute_success_by_shortname` - получение курса по короткому имени
4. `test_moodle_execute_success_no_payload` - работа с credentials без payload (обратная совместимость)
5. `test_moodle_execute_url_with_trailing_slash` - обработка URL с trailing slash
6. `test_moodle_execute_alternative_credential_keys` - поддержка альтернативных ключей в credentials

### ❌ Обработка ошибок:
7. `test_moodle_execute_no_credentials` - отсутствие credentials
8. `test_moodle_execute_missing_url` - отсутствие URL в credentials
9. `test_moodle_execute_missing_token` - отсутствие токена в credentials
10. `test_moodle_execute_missing_value` - отсутствие обязательного параметра value
11. `test_moodle_execute_invalid_field` - невалидное значение поля field
12. `test_moodle_execute_moodle_api_error` - ошибка от Moodle API
13. `test_moodle_execute_http_status_error` - HTTP статус ошибка (404, 500 и т.д.)
14. `test_moodle_execute_request_error` - ошибка сетевого запроса
15. `test_moodle_execute_unexpected_error` - неожиданная ошибка

## Результаты последнего запуска

```
============================= test session starts =============================
15 passed in 2.75s
=============================
```

**Статус**: ✅ Все тесты пройдены успешно

## Используемые моки

- `httpx.AsyncClient` - мокируется для имитации HTTP запросов
- `CredentialsResolver` - мокируется для тестирования различных сценариев credentials
- `BotLogger` - мокируется для проверки логирования ошибок

## Примеры тестовых данных

### Успешный ответ Moodle API:
```python
{
    "courses": [
        {
            "id": 5,
            "shortname": "MATH101",
            "fullname": "Mathematics 101",
            "idnumber": "COURSE-2024-001",
            "summary": "Introduction to Mathematics",
            "categoryid": 1
        }
    ]
}
```

### Ошибка Moodle API:
```python
{
    "exception": "moodle_exception",
    "errorcode": "invalidtoken",
    "message": "Invalid token"
}
```

## Примечания

- Тесты используют `--noconftest` для изоляции от основного conftest.py проекта
- Все тесты асинхронные и используют `@pytest.mark.asyncio`
- Моки настроены для проверки правильности формирования HTTP запросов к Moodle API

