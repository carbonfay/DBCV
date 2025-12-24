# YooKassa — Live run results (DBCV)

## Overview
This document summarizes the live runs performed against YooKassa using the shop id and API key you provided. It contains what succeeded, what failed, concrete request and response examples, and short explanations about the cause and recommended follow-ups.

> Files produced during runs:
> - `scripts/youkassa_live_results.json` — payments list result
> - `scripts/youkassa_create_standalone_results.json` — standalone receipts attempts

---

## 1) youkassa_get_payments
- Action performed: GET /payments (limit=20)
- Request (example):

GET https://api.yookassa.ru/v3/payments?limit=20
Authorization: Basic <base64(shop_id:api_key)>

- Live response (excerpt from `scripts/youkassa_live_results.json`):

{
  "type": "list",
  "items": []
}

- Result: No payments were returned by the API.
- Explanation: The account currently has zero payments matching the request (no items in the list). This blocked follow-up actions which require binding receipts to payment IDs.
- Next steps: Re-run with broader filters (increase `limit` up to 100 and/or add date range or status filter such as `succeeded`, `paid`, `waiting_for_capture`) to try to find payments for receipt creation.

---

## 2) youkassa_get_payment
- Action performed: GET /payments/{payment_id}
- Actual behavior during live run: Executed only if a payment was found; no payments were found in step (1), so the action was not invoked.
- Recommendation: When payments are found, run GET /payments/{id} to fetch full details and then create receipts bound to those payment IDs.

---

## 3) youkassa_create_receipt (standalone / attempts)
We attempted multiple strategies to create receipts:

- First, attempts to create receipts with minimal payloads failed validation (missing `settlements` and `customer`).
- We added `settlements` and `customer` and were then required to include `Idempotence-Key` header per request.
- After adding idempotence keys and using `type` attempts, the API still rejected standalone receipts with a parameter error on `type`.

Example request (payload used, with `send=false`):

POST https://api.yookassa.ru/v3/receipts
Headers:
  Authorization: Basic <base64(shop_id:api_key)>
  Idempotence-Key: <random-uuid-hex>

Body:
{
  "type": "sell",                 # tried 'payment' and 'sell' (both rejected in our tests)
  "external_id": "dbcv-test-...",
  "send": false,
  "items": [ ... ],
  "settlements": [{"type": "bank_card", "amount": {"value":"1.00","currency":"RUB"}}],
  "customer": {"phone": "+79000000000"}
}

Example responses (excerpt from `scripts/youkassa_create_standalone_results.json`):

{
  "type": "error",
  "id": "019b51a3-5520-7e33-adef-e049bb2387f2",
  "description": "Invalid parameter's value (...)",
  "parameter": "type",
  "code": "invalid_request"
}

- Result: Standalone receipts creation failed. The API requires stricter/alternative payloads or receipts to be bound to actual payments.
- Root causes & notes:
  - Missing `settlements`/`customer` validation errors were resolved by adding minimal fields.
  - YooKassa requires `Idempotence-Key` header for create operations — added and then observed further validation errors.
  - The `type` parameter for standalone receipts is not accepted in the tested form, suggesting the service expects receipts to be created via attachment to payment IDs (preferred path) or specific documented parameters for 'sell' flows (we couldn't find an accepted parameter combination in live tests with this account).

- Recommendation: Use **existing payment IDs** to create receipts (POST /receipts with `payment_id`), or consult YooKassa documentation / account settings for the correct `type` and required fields for standalone receipts (it may be limited or account-specific). The most reliable path is: find payments → create receipts attached to them (send=false).

---

## Repro steps & files
- Scripts used (repo):
  - `scripts/run_yookassa_live.py` — lists payments and tries to fetch a specific payment if found
  - `scripts/create_standalone_receipts.py` — attempts to create two standalone receipts (we iterated and added headers/fields as needed)
- Output files:
  - `scripts/youkassa_live_results.json` — payments list output
  - `scripts/youkassa_create_standalone_results.json` — attempts to create receipts with responses

---

## Suggested next steps (for reviewer)
- Re-run listing with `limit=100` and date filters (e.g., last 30 days) and search for statuses `succeeded`, `paid`, or `waiting_for_capture`.
- Once payment IDs are found, call `create receipt` with `payment_id` set and `send=false`.
- If standalone receipts are required, consult YooKassa docs or account settings for the correct payload (some parameters may be account-dependent).

---

If you want, I can commit this file to a new branch, add comments to commits referencing the live-run files, and push for review — confirm and I'll push now.
