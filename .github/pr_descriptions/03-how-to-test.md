# How to Test

## Create payment
- Call integration `youkassa_create_payment` with:
```
{
  "amount": {"value": "100.00", "currency": "RUB"},
  "description": "Test payment",
  "capture": true,
  "confirmation": {"type": "redirect", "return_url": "https://example.com/return"},
  "payment_method_data": {"type": "bank_card"}
}
```
- Expect `ok: true` and `result.id` (payment_id).
- See request/response details in logs and `_debug`.

## Create receipt
- Call `youkassa_create_receipt` with:
```
{
  "payment_id": "<result.id>",
  "type": "payment",
  "send": true,
  "items": [
    {"description": "Product", "quantity": 1, "amount": {"value": "100.00", "currency": "RUB"}, "vat_code": 1}
  ]
}
```
- If `settlements` omitted, integration auto-fills to match items total.
- Check logs for full request/response; `_debug` includes headers and status.

## Logs
- Backend container logs: `docker-compose logs -f backend`.
- Frontend bot log panel: shows `=== YooKassa ... Request/Response ===` blocks.
