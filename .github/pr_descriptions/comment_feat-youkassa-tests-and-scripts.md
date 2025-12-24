# Live-run comment — feat/youkassa-tests-and-scripts

**Добавленные скрипты и результаты**

- `scripts/run_yookassa_live.py` — делает `GET /payments` и при найденном ID делает `GET /payments/{id}` (реализация на stdlib, чтобы не требовать установки сторонних пакетов).
- `scripts/create_standalone_receipts.py` — пытается создать 2 standalone-чека, добавляя `settlements`, `customer`, `Idempotence-Key` и логируя ответы.
- `scripts/test_yookassa_connection.py` — demo runner, использующий фикстуры (offline).

**Результаты live-прогона (summary):**

- `GET /payments?limit=20` → `items: []` (см. `scripts/youkassa_live_results.json`)
- Попытки создания standalone-чеки → валидация/ошибки (см. `scripts/youkassa_create_standalone_results.json`)
- Сценарии для воспроизведения и примеры запросов/ответов описаны в `.github/pr_descriptions/youkassa-live-results.md`

**Как воспроизвести (PowerShell):**

```powershell
$env:YOOKASSA_SHOP_ID='1236220'; $env:YOOKASSA_API_KEY='test_...'; python .\scripts\run_yookassa_live.py
$env:YOOKASSA_SHOP_ID='1236220'; $env:YOOKASSA_API_KEY='test_...'; python .\scripts\create_standalone_receipts.py
python scripts/test_yookassa_connection.py  # demo using fixtures
python -m pytest backend/app/tests/integrations -q  # unit tests
```

**Рекомендация:** основная рабочая траектория — найти реальные `payment_id` (через расширенный `GET /payments`) и затем создать чеки с `payment_id` и `send=false`. Скрипты и сохранённые результаты (`scripts/*.json`) помогут ревьюерам воспроизвести поведение.

**Файлы / доказательства:**

- `scripts/run_yookassa_live.py`
- `scripts/create_standalone_receipts.py`
- `scripts/youkassa_live_results.json`
- `scripts/youkassa_create_standalone_results.json`
- `scripts/youkassa_test_results.json`