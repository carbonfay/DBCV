# PR: Gitverse Get Merge Request

## Описание
Реализована интеграция **Gitverse Get Merge Request** — получение информации о pull/merge request из GitHub через библиотеку PyGithub.

## Изменения
- Добавлен файл `backend/app/integrations/gitverse/get_merge_request.py`
- Зарегистрирована интеграция в `backend/app/integrations/gitverse/__init__.py`
- Добавлены тесты: `backend/app/tests/integrations/test_gitverse_get_merge_request.py`

## Тестирование
- [x] Проверен синтаксис Python
- [x] Протестирована через API (`/api/integrations/catalog`)
- [x] Протестирована в боте (создан Connection Group, выполнена интеграция)
- [x] Проверена визуально на фронте
- [x] Проверена документация

## Видео
[Ссылка на видео с демонстрацией]

## Чеклист
- [x] Код следует стилю проекта
- [x] Используется правильная библиотека из SAFE_LIBRARIES.md (PyGithub)
- [x] Credentials получаются через `CredentialsResolver`
- [x] Обработка ошибок реализована (логирование и корректные ответы в `response`)
- [x] Метаданные заполнены полностью (id, name, description, category, icon_s3_key, config_schema)
- [x] Добавлены примеры использования в `examples`
- [x] Версия указана корректно ("1.0.0")

---

### Дополнительно
- **Ветка:** `integration/gitverse/get_merge_request.py/gusev`
- **PR:** https://github.com/carbonfay/DBCV/pull/new/integration/gitverse/get_merge_request.py/gusev

> Примечание: Git при добавлении показал предупреждение про вложенный репозиторий `DBCV_Builder`. Если это не нужно, можно удалить его из индекса перед следующим коммитом: `git rm --cached DBCV_Builder`.
