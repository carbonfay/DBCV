# Интеграция Medicine: Get Articles

## Обзор

Интеграция получает медицинские статьи через прямые HTTP-запросы (используется `httpx`).

## Файлы

- `backend/app/integrations/medicine/__init__.py`
- `backend/app/integrations/medicine/get_articles.py`

## Используемая библиотека

`httpx>=0.27.0`

## Credentials

- provider: `medicine`
- strategy: `api_key`
- payload:
```json
{
  "api_key": "YOUR_API_KEY",
  "api_key_header": "X-API-Key"
}
```

## Config (примеры)

- `{"base_url": "http://localhost:8003"}`
- `{"base_url": "http://localhost:8003", "query": "cardiology", "page": 1, "page_size": 10}`
- `{"base_url": "http://localhost:8003", "category": "research", "sort": "recent"}`

## Тесты

Тесты лежат в `backend/app/tests/integrations/`.

### Требования к окружению для запуска тестов

- Установить зависимости backend (включая dev-зависимости).
- Убедиться, что `PYTHONPATH` указывает на `backend`:

```powershell
$env:PYTHONPATH="C:\Users\Tavadin\Desktop\test\DBCV\backend"
pytest
```

## Проверка (через фронт/логи)

- В логах backend есть `GET /api/v1/integrations/catalog` со статусом `200 OK`.
- В логах backend есть `GET /api/v1/integrations/medicine_get_articles/metadata` со статусом `200 OK`.
