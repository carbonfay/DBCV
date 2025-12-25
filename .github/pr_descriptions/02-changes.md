# Changes

- `backend/app/integrations/youkassa/create_payment.py`
  - Added HTTP POST `/v3/payments` with Basic Auth.
  - Enhanced config schema, removed empty objects from body.
  - Added full diagnostics in logs and response `_debug`.
- `backend/app/integrations/youkassa/create_receipt.py`
  - Added HTTP POST `/v3/receipts` with Basic Auth.
  - Use unique `Idempotence-Key` (UUID) per request.
  - Auto-compute and inject `settlements` if not provided.
  - Added full diagnostics logging and `_debug` in responses.
- `backend/app/loggers/bot.py`
  - Implemented `debug()` method so integrations can log at DEBUG level.
- Removed Python test files across repo (root scripts/tests, backend/mcp, backend/app/tests).
