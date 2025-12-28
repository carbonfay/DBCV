# Проверка интеграции Medicine Get Articles

## Проверка в backend

- Запуск API:
  - `GET /api/v1/integrations/catalog` - `200 OK`
  - `GET /api/v1/integrations/medicine_get_articles/metadata` - `200 OK`
  - `GET /api/v1/articles?query=diabetes&page=1&page_size=5` - `200 OK`

## Проверка через фронт

- В UI создан шаг интеграции Medicine Get Articles.
- Запрос выполняется и возвращает `response.ok = true` с `result` (список статей).

# Проверка интеграции Medicine Get Clinical Trials

## Проверка в backend

- Запуск API:
  - `GET /api/v1/integrations/catalog` - `200 OK`
  - `GET /api/v1/integrations/medicine_get_trials/metadata` - `200 OK`
  - `GET /api/v1/trials?condition=diabetes&page=1&page_size=5` - `200 OK`

## Проверка через фронт

- В UI создан шаг интеграции Medicine Get Clinical Trials.
- Запрос выполняется и возвращает `response.ok = true` с `result` (список исследований).
