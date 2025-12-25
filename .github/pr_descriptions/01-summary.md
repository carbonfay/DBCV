# PR Summary

- Switch YooKassa integrations to direct HTTP for `create_payment` and `create_receipt`.
- Add detailed request/response diagnostics: status, headers, raw body, parsed JSON.
- Fix idempotence handling in receipts: per-request UUID instead of `payment_id`.
- Auto-fill `settlements` in receipt when missing by summing `items`.
- Remove legacy test files to reduce noise.
