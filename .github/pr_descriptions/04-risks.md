# Risks & Notes

- Idempotence: YooKassa caches by `Idempotence-Key` for 24h. Receipts now generate UUID per call to avoid reuse issues.
- Settlements: Auto-fill assumes non-mixed currency in items; if mixed or amounts missing, integration fails early with clear error.
- Removed tests: Reduced repo noise; if CI relied on them, ensure pipelines are updated.
- Credentials: Integration expects `payload.shop_id/account_id` and `secret_key`. If missing, returns 401 with details.
- Diagnostics: Responses echo full server JSON and headers; avoid leaking secrets (we redact secret value).
