# Интеграция Moodle Get Courses

## Описание
Реализована интеграция **Moodle Get Courses** для получения списка курсов из Moodle Learning Management System через Web Services API. Интеграция позволяет получать все доступные курсы или фильтровать их по ID курсов.

## Изменения
- Добавлен файл `backend/app/integrations/moodle_2/get_courses.py` - основная реализация интеграции
- Зарегистрирована интеграция в `backend/app/integrations/moodle_2/__init__.py`
- Добавлен импорт в `backend/app/integrations/__init__.py` для автоматической регистрации
- Добавлены мок-тесты: `backend/app/tests/integrations/moodle/mock_2/test_get_courses.py` (19 тестов)
- Добавлена документация: `backend/app/tests/integrations/moodle/mock_2/README.md`
- Добавлен отчет о проверке: `backend/app/integrations/moodle_2/VERIFICATION_REPORT.md`

## Технические детали

### Используемая библиотека
- **httpx** - для прямых HTTP запросов к Moodle Web Services API (рекомендуется в SAFE_LIBRARIES.md)

### Credentials
- **Provider**: `other` (так как провайдера Moodle не существует в системе)
- **Strategy**: `api_key`
- **Требуемые поля в credentials**:
  - `url` или `moodle_url` или `server_url` - URL сервера Moodle
  - `token` или `wstoken` или `api_key` - токен Web Services

### API функция
- **Moodle Web Service**: `core_course_get_courses`
- **Endpoint**: `{moodle_url}/webservice/rest/server.php`
- **Метод**: GET
- **Параметры**:
  - `wstoken` - токен Web Services
  - `wsfunction` - имя функции API (`core_course_get_courses`)
  - `moodlewsrestformat` - формат ответа (json)
  - `options[ids][0]`, `options[ids][1]`, ... - опциональные ID курсов для фильтрации

### Параметры конфигурации
- `course_ids` (optional, array of integers) - массив ID курсов для фильтрации. Если не указан, возвращаются все курсы

## Тестирование
- [x] Проверен синтаксис Python (`python -m py_compile`)
- [x] Проверена регистрация интеграции в реестре
- [x] Протестирована через мок-тесты (19 тестов, все пройдены)
- [ ] Протестирована через API (`/api/integrations/catalog`)
- [ ] Протестирована в боте (создан Connection Group, выполнена интеграция)
- [ ] Проверена визуально на фронте
- [x] Проверена документация

### Результаты мок-тестов
```
19 passed in 4.03s
```

**Покрытие тестами:**
- ✅ Успешные сценарии (9 тестов): получение всех курсов, фильтрация по ID, обработка различных форматов credentials
- ✅ Обработка ошибок (10 тестов): отсутствие credentials, невалидные параметры, ошибки API, сетевые ошибки

## Примеры использования

### Пример 1: Получить все курсы
```json
{}
```

### Пример 2: Получить курсы по ID
```json
{
  "course_ids": [1, 2, 5]
}
```

### Пример 3: Получить один курс по ID
```json
{
  "course_ids": [5]
}
```

## Видео
[Ссылка на видео с демонстрацией]

## Чеклист
- [x] Код следует стилю проекта
- [x] Используется правильная библиотека из SAFE_LIBRARIES.md (httpx)
- [x] Credentials получаются через CredentialsResolver
- [x] Обработка ошибок реализована (HTTP ошибки, ошибки Moodle API, сетевые ошибки, неожиданные ошибки, валидация параметров)
- [x] Метаданные заполнены полностью:
  - [x] id: "moodle_get_courses"
  - [x] name: "Moodle Get Courses"
  - [x] description: "Получение списка курсов из Moodle. Можно получить все курсы или отфильтровать по ID"
  - [x] category: "education"
  - [x] icon_s3_key: "icons/integrations/moodle.svg"
  - [x] color: "#f98012"
  - [x] config_schema: полная JSON Schema с опциональным параметром course_ids (массив целых чисел)
- [x] Добавлены примеры использования в examples (3 примера)
- [x] Версия указана корректно ("1.0.0")
- [x] Интеграция зарегистрирована в реестре
- [x] Добавлены мок-тесты с полным покрытием сценариев
- [x] Обработка различных форматов credentials (payload, без payload, альтернативные ключи)
- [x] Валидация параметров (проверка типа course_ids, проверка элементов массива)

## Дополнительная информация

### Особенности реализации
1. **Поддержка различных форматов credentials**: интеграция поддерживает credentials как с `payload`, так и без него (обратная совместимость)
2. **Гибкие ключи credentials**: поддерживаются альтернативные названия ключей (`url`/`moodle_url`/`server_url`, `token`/`wstoken`/`api_key`)
3. **Обработка trailing slash**: автоматическое удаление trailing slash из URL сервера Moodle
4. **Детальная обработка ошибок**: отдельная обработка ошибок Moodle API, HTTP ошибок, сетевых ошибок
5. **Валидация параметров**: проверка типа и содержимого массива `course_ids`
6. **Гибкая фильтрация**: возможность получить все курсы или отфильтровать по списку ID

### Файлы в коммите
- `backend/app/integrations/moodle_2/get_courses.py` (227 строк)
- `backend/app/integrations/moodle_2/__init__.py` (10 строк)
- `backend/app/integrations/__init__.py` (обновлен)
- `backend/app/integrations/moodle_2/VERIFICATION_REPORT.md`
- `backend/app/tests/integrations/moodle/mock_2/test_get_courses.py` (617 строк)
- `backend/app/tests/integrations/moodle/mock_2/__init__.py`
- `backend/app/tests/integrations/moodle/mock_2/conftest.py`
- `backend/app/tests/integrations/moodle/mock_2/README.md`

**Всего**: 8 файлов, 342+ строк добавлено

### Отличия от moodle_get_course

Интеграция `moodle_get_courses` отличается от `moodle_get_course`:

- **Функция API**: `core_course_get_courses` (вместо `core_course_get_courses_by_field`)
- **Параметры**: опциональный массив `course_ids` (вместо обязательных `field` и `value`)
- **Результат**: всегда возвращает массив курсов (даже если фильтруется по одному ID)
- **Использование**: для получения списка курсов или множественной выборки по ID

