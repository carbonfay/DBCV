# Live-run comment — feat/youkassa-receipt-create

**Live-run — youkassa_create_receipt (POST /receipts)**

Цель: создать 2 чека (`send=false`). Проверяли standalone-формат (без `payment_id`) и минимальный набор полей.

**Что я отправлял (пример payload):**

```json
{
  "type": "sell",
  "external_id": "dbcv-test-...",
  "send": false,
  "items": [
    {"description":"Test","quantity":1,"amount":{"value":"1.00","currency":"RUB"},"vat_code":"2"}
  ],
  "settlements":[{"type":"bank_card","amount":{"value":"1.00","currency":"RUB"}}],
  "customer":{"phone":"+79000000000"}
}
```

Заголовки: `Authorization: Basic <...>`, `Idempotence-Key: <uuid>`

**Что произошло (live-ошибки):**

1. Первые попытки отклонил API: отсутствовали `settlements`/`customer` — добавили минимальные поля.
2. API потребовал `Idempotence-Key` — добавили уникальный ключ на каждый запрос.
3. После этого API вернул ошибку по `parameter: "type"` (`invalid_request`) — standalone payload был отклонён.

**Пример ответа (фрагмент):**

```json
{
  "type": "error",
  "id": "019b51a3-...",
  "description": "Invalid parameter's value ...",
  "parameter": "type",
  "code": "invalid_request"
}
```

**Вывод:** standalone-чек в нашем тестовом аккаунте **не принимается** в сочетании с пробованными параметрами. Наиболее надёжный путь: создавать чеки, привязанные к `payment_id` (POST /receipts с `payment_id` и `send=false`). Если standalone-чек обязателен, нужно уточнить у YooKassa корректный payload или права / настройки аккаунта (параметры могут быть account-specific).

**Файлы / доказательства:**

- `scripts/youkassa_create_standalone_results.json` (все ответы и idempotence keys)
- `.github/pr_descriptions/youkassa-live-results.md` (анализ)

**Рекомендация:** предоставить реальные `payment_id`, чтобы я создал чеки, привязанные к платежам, и приложил успешный ответ в PR.