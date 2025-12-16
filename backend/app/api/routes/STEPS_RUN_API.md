# Step Run API (интеграции)

Этот endpoint позволяет выполнить интеграционный блок (или все интеграционные блоки) внутри `step` напрямую из фронта — без запуска всего бота/флоу.

## POST `/api/v1/steps/{step_id}/run`

Выполняет все `connection_groups` у `step`, у которых `search_type="integration"`.  
Если передать `connection_group_id`, выполнит только один блок.

### Body

```json
{
  "context": {},
  "all_variables": {},
  "connection_group_id": null,
  "credentials": [
    {
      "provider": "telegram",
      "strategy": "api_key",
      "payload": { "api_key": "..." }
    }
  ]
}
```

### Ответ

- `results[]` — результат каждого выполненного integration-блока (то, что вернул `integration.execute()`).
- `all_variables` — обновлённые переменные после применения `connection_group.variables` (если они настроены).
- `logs` — собранные логи выполнения.

### Пример (curl)

```bash
curl -X POST "http://localhost:8003/api/v1/steps/<STEP_ID>/run" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "context": {},
    "all_variables": {},
    "credentials": []
  }'
```
