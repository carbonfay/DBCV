# Moodle Create Course Integration

## Описание
Реализована интеграция Moodle Create Course для создания новых курсов в системе Moodle через Web Services API.

Интеграция позволяет:
- Создавать новые курсы в Moodle с настраиваемыми параметрами
- Указывать полное и краткое название курса
- Настраивать категорию, формат, видимость курса
- Устанавливать даты начала и окончания курса
- Добавлять описание курса с поддержкой HTML
- Настраивать язык и количество разделов

## Изменения
- Добавлен файл `backend/app/integrations/moodle/create_course.py`
- Зарегистрирована интеграция в `backend/app/integrations/moodle/__init__.py`
- Добавлен импорт в `backend/app/integrations/__init__.py`
- Добавлены мок-тесты: `backend/app/integrations/tests/mocks/test_moodle_create_course.py`

## Технические детали

### Библиотека
- Используется `httpx` для прямых HTTP запросов к Moodle Web Services API
- Рекомендация из `SAFE_LIBRARIES.md`: использовать httpx вместо неофициальных библиотек

### Credentials
- **Provider**: `other`
- **Strategy**: `api_key`
- **Требуемые поля**:
  - `api_key` (или `token`, `wstoken`) - API токен Moodle
  - `moodle_url` (или `url`, `base_url`) - URL сервера Moodle

### Параметры конфигурации

**Обязательные:**
- `fullname` (string) - Полное название курса
- `shortname` (string) - Краткое название курса (уникальное)
- `categoryid` (integer) - ID категории курса

**Опциональные:**
- `summary` (string) - Описание курса (HTML поддерживается)
- `summaryformat` (integer) - Формат описания: 0=MOODLE, 1=HTML, 2=PLAIN, 4=MARKDOWN
- `format` (string) - Формат курса: "topics", "weeks", "social", "singleactivity"
- `startdate` (integer) - Дата начала курса (UNIX timestamp)
- `enddate` (integer) - Дата окончания курса (UNIX timestamp)
- `visible` (integer) - Видимость курса: 0=скрыт, 1=видим
- `lang` (string) - Язык курса (например, 'ru', 'en')
- `numsections` (integer) - Количество разделов (для форматов topics и weeks)

### API Endpoint
- **Moodle Web Service**: `core_course_create_courses`
- **URL формат**: `{moodle_url}/webservice/rest/server.php`
- **Метод**: POST
- **Формат**: JSON (moodlewsrestformat=json)

## Тестирование

### Мок-тесты
- [x] Проверен синтаксис Python
- [x] Все 15 мок-тестов проходят успешно
- [x] Покрытие основных сценариев:
  - Успешное создание курса
  - Обработка различных форматов credentials
  - Нормализация URL
  - Обработка ошибок (Moodle API, HTTP, сетевые)
  - Валидация обязательных параметров
  - Работа с опциональными параметрами

### Функциональное тестирование
- [ ] Проверена через API (`/api/integrations/catalog`)
- [ ] Протестирована в боте (создан Connection Group, выполнена интеграция)
- [ ] Проверена визуально на фронте
- [ ] Проверена документация

## Видео
[Ссылка на видео с демонстрацией]

## Примеры использования

### Пример 1: Простой курс
```json
{
  "fullname": "Введение в Python",
  "shortname": "python101",
  "categoryid": 1,
  "summary": "Базовый курс по программированию на Python",
  "format": "topics",
  "visible": 1
}
```

### Пример 2: Курс с датами
```json
{
  "fullname": "Продвинутый Python",
  "shortname": "python201",
  "categoryid": 1,
  "summary": "Продвинутый курс по Python",
  "format": "weeks",
  "startdate": 1704067200,
  "enddate": 1735689600,
  "numsections": 12,
  "visible": 1
}
```

## Чеклист
- [x] Код следует стилю проекта
- [x] Используется правильная библиотека из SAFE_LIBRARIES.md (httpx)
- [x] Credentials получаются через CredentialsResolver
- [x] Обработка ошибок реализована (Moodle API, HTTP, сетевые ошибки)
- [x] Метаданные заполнены полностью (id, name, description, category, icon_s3_key, config_schema)
- [x] Добавлены примеры использования в examples (2 примера)
- [x] Версия указана корректно ("1.0.0")
- [x] Поддержка различных форматов credentials (payload, альтернативные ключи, обратная совместимость)
- [x] Нормализация URL Moodle (автоматическое добавление пути к Web Services)
- [x] Валидация обязательных параметров
- [x] Поддержка всех опциональных параметров Moodle API

## Особенности реализации

1. **Нормализация URL**: Интеграция автоматически добавляет путь `/webservice/rest/server.php` к URL Moodle, если он не указан полностью.

2. **Гибкая работа с credentials**: Поддерживаются различные варианты ключей:
   - `api_key`, `token`, `wstoken` для API ключа
   - `moodle_url`, `url`, `base_url` для URL сервера

3. **Обработка ошибок**: 
   - Ошибки Moodle API (exception, errorcode, message)
   - HTTP ошибки (статус коды)
   - Сетевые ошибки (таймауты, недоступность сервера)
   - Неожиданные форматы ответа

4. **Формат ответа Moodle API**: 
   - При успехе: `{"id": course_id}` или `[{"id": course_id}]`
   - При ошибке: `{"exception": "...", "errorcode": "...", "message": "..."}`

## Связанные файлы

- `backend/app/integrations/moodle/create_course.py` - Основная реализация
- `backend/app/integrations/moodle/__init__.py` - Регистрация интеграции
- `backend/app/integrations/tests/mocks/test_moodle_create_course.py` - Мок-тесты
- `backend/app/integrations/SAFE_LIBRARIES.md` - Документация по безопасным библиотекам

