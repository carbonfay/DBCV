# Мок-тесты для Moodle Get Courses интеграции

## Описание

Мок-тесты для проверки работы интеграции `MoodleGetCoursesIntegration` без реальных HTTP запросов к Moodle API.

## Структура тестов

### Файлы:
- `test_get_courses.py` - основные тесты интеграции (19 тестов)
- `conftest.py` - конфигурация pytest
- `__init__.py` - инициализация пакета

## Запуск тестов

### Вариант 1: С опцией --noconftest (рекомендуется)
```bash
cd backend
python -m pytest app/tests/integrations/moodle/mock_2/test_get_courses.py -v --noconftest
```

### Вариант 2: Через скрипт
```bash
cd backend
python app/tests/integrations/moodle/mock_2/run_tests.py
```

## Покрытие тестами

Всего тестов: **19**

### ✅ Успешные сценарии (7 тестов):
1. `test_moodle_get_courses_metadata` - проверка метаданных интеграции
2. `test_moodle_get_courses_success_all_courses` - получение всех курсов (без фильтрации)
3. `test_moodle_get_courses_success_filtered_by_ids` - получение курсов по ID
4. `test_moodle_get_courses_success_single_course` - получение одного курса по ID
5. `test_moodle_get_courses_success_no_payload` - работа с credentials без payload (обратная совместимость)
6. `test_moodle_get_courses_url_with_trailing_slash` - обработка URL с trailing slash
7. `test_moodle_get_courses_alternative_credential_keys` - поддержка альтернативных ключей в credentials
8. `test_moodle_get_courses_empty_course_ids_array` - обработка пустого массива course_ids
9. `test_moodle_get_courses_large_course_ids_list` - обработка большого списка course_ids

### ❌ Обработка ошибок (10 тестов):
10. `test_moodle_get_courses_no_credentials` - отсутствие credentials
11. `test_moodle_get_courses_missing_url` - отсутствие URL в credentials
12. `test_moodle_get_courses_missing_token` - отсутствие токена в credentials
13. `test_moodle_get_courses_invalid_course_ids_not_list` - невалидный тип course_ids (не массив)
14. `test_moodle_get_courses_invalid_course_ids_not_integers` - course_ids содержит не числа
15. `test_moodle_get_courses_course_ids_with_mixed_types` - смешанные типы в course_ids
16. `test_moodle_get_courses_moodle_api_error` - ошибка от Moodle API
17. `test_moodle_get_courses_http_status_error` - HTTP статус ошибка (404, 500 и т.д.)
18. `test_moodle_get_courses_request_error` - ошибка сетевого запроса
19. `test_moodle_get_courses_unexpected_error` - неожиданная ошибка

## Результаты последнего запуска

```
============================= test session starts =============================
19 passed in 4.03s
=============================
```

**Статус**: ✅ Все тесты пройдены успешно

## Используемые моки

- `httpx.AsyncClient` - мокируется для имитации HTTP запросов
- `CredentialsResolver` - мокируется для тестирования различных сценариев credentials
- `BotLogger` - мокируется для проверки логирования ошибок

## Примеры тестовых данных

### Успешный ответ Moodle API (все курсы):
```python
{
    "courses": [
        {
            "id": 1,
            "shortname": "MATH101",
            "fullname": "Mathematics 101",
            "categoryid": 1
        },
        {
            "id": 2,
            "shortname": "PHYS201",
            "fullname": "Physics 201",
            "categoryid": 1
        }
    ]
}
```

### Успешный ответ Moodle API (фильтрация по ID):
```python
{
    "courses": [
        {
            "id": 1,
            "shortname": "MATH101",
            "fullname": "Mathematics 101"
        },
        {
            "id": 5,
            "shortname": "CHEM301",
            "fullname": "Chemistry 301"
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

## Особенности тестирования

### Параметры запроса

Интеграция использует Moodle Web Services API функцию `core_course_get_courses`:

- **Без фильтрации**: запрос без параметров `options[ids]`
- **С фильтрацией**: запрос с параметрами `options[ids][0]`, `options[ids][1]`, и т.д.

### Валидация параметров

Тесты проверяют:
- `course_ids` должен быть массивом
- Все элементы `course_ids` должны быть целыми числами
- Пустой массив `course_ids` обрабатывается как отсутствие фильтрации

## Примечания

- Тесты используют `--noconftest` для изоляции от основного conftest.py проекта
- Все тесты асинхронные и используют `@pytest.mark.asyncio`
- Моки настроены для проверки правильности формирования HTTP запросов к Moodle API
- Тесты проверяют корректность передачи параметров фильтрации по ID курсов

