# Live-run comment — feat/youkassa-payments-list

**Live-run — youkassa_get_payments (GET /payments)**

Я выполнил live-прогон списка платежей с вашими тестовыми креденшелами.

**Запрос (пример):**

```
GET https://api.yookassa.ru/v3/payments?limit=20
Authorization: Basic <base64(shop_id:api_key)>
```

**Live-ответ (фрагмент):**

```json
{
  "type": "list",
  "items": []
}
```

**Что получилось:** API вернул пустой список платежей (`items: []`), то есть в аккаунте нет платежей, подходящих под этот запрос.

**Почему:** платежи либо отсутствуют за указанный период / с текущими фильтрами, либо нужно увеличить выборку/фильтры.

**Рекомендации:**

- Повторить `GET /payments` с `limit=100` и/или добавить фильтры: `status` = `succeeded|paid|waiting_for_capture` и/или date range (last 30 days).
- Если есть конкретные `payment_id`, пришлите их — я выполню `GET /payments/{id}` и добавлю ответ в PR.

**Файлы / доказательства:**

- `.github/pr_descriptions/youkassa-live-results.md` (подробный отчёт)
- `scripts/youkassa_live_results.json` (экспорт ответа)

---

Если хотите, могу сам повторить запрос с расширенными фильтрами и прикрепить результаты в этот PR.