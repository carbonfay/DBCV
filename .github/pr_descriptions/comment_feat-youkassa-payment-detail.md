# Live-run comment — feat/youkassa-payment-detail

**Live-run — youkassa_get_payment (GET /payments/{id})**

План был: взять `payment_id` из шага списка и выполнить `GET /payments/{id}`.

**Фактическое поведение:** `GET /payments` вернул `items: []`, поэтому `GET /payments/{id}` не выполнялся (нет ID для запроса).

**Пример запроса (если будет ID):**

```
GET https://api.yookassa.ru/v3/payments/{payment_id}
Authorization: Basic <base64(shop_id:api_key)>
```

**Пример ожидаемого ответа (fixture):**

```json
{
  "id": "pay_1",
  "status": "succeeded",
  "amount": {"value": "100.00", "currency": "RUB"},
  "created_at": "2025-12-01T12:00:00Z"
}
```

**Рекомендация:** либо предоставьте `payment_id`, либо разрешите мне повторить `GET /payments` с `limit=100` и/или фильтрами по статусам/датам; затем я выполню `GET /payments/{id}` и приложу реальный ответ в PR.

**Файлы / доказательства:**

- `backend/app/tests/fixtures/youkassa/payment_detail.json` (fixture)
- `scripts/youkassa_live_results.json` (пока что пустой список)

---

Готов выполнить `GET /payments` с расширением фильтров и добавить реальный пример ответа в PR при нахождении `payment_id`.