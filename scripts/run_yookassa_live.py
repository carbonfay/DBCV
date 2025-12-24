"""Run live YooKassa requests: list payments, get payment, create receipts.

Usage (PowerShell):
  $env:YOOKASSA_SHOP_ID='1236220'; $env:YOOKASSA_API_KEY='test_...'; python scripts/run_yookassa_live.py

Notes:
- This script reads credentials from environment variables and does not store them.
- It will create receipts with send=False to avoid notifications.
- Uses only Python stdlib (no external dependencies required).
"""
import os
import json
import base64
from typing import Any, Dict, List
from urllib import request, parse, error

API_BASE = "https://api.yookassa.ru/v3"

SHOP_ID = os.environ.get("YOOKASSA_SHOP_ID")
API_KEY = os.environ.get("YOOKASSA_API_KEY")

if not SHOP_ID or not API_KEY:
    raise SystemExit("YOOKASSA_SHOP_ID and YOOKASSA_API_KEY must be set as environment variables")

BASIC_AUTH = base64.b64encode(f"{SHOP_ID}:{API_KEY}".encode()).decode()
HEADERS = {"Accept": "application/json", "Content-Type": "application/json", "Authorization": f"Basic {BASIC_AUTH}"}

results: List[Dict[str, Any]] = []


def do_get(path: str, params: Dict[str, Any] = None):
    url = f"{API_BASE}{path}"
    if params:
        url = url + "?" + parse.urlencode(params)

    req = request.Request(url, headers=HEADERS, method="GET")
    try:
        with request.urlopen(req, timeout=30) as resp:
            data = resp.read().decode()
            return json.loads(data)
    except error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {"status_code": e.code, "text": str(e)}
    except Exception as e:
        return {"error": str(e)}


def do_post(path: str, body: Dict[str, Any]):
    url = f"{API_BASE}{path}"
    data = json.dumps(body).encode()
    req = request.Request(url, data=data, headers=HEADERS, method="POST")
    try:
        with request.urlopen(req, timeout=30) as resp:
            data = resp.read().decode()
            return json.loads(data)
    except error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {"status_code": e.code, "text": str(e)}
    except Exception as e:
        return {"error": str(e)}


# 1) List payments
print("\n--- Listing Payments ---")
payments_json = do_get("/payments", params={"limit": 20})
print(json.dumps(payments_json, indent=2, ensure_ascii=False))
results.append({"integration": "youkassa_get_payments", "request": {"limit": 20}, "response": payments_json})

# select up to 2 payments suitable for receipts
payments_list = payments_json.get("items") if isinstance(payments_json, dict) else None
selected = []
if payments_list:
    for p in payments_list:
        if p.get("status") in ("succeeded", "waiting_for_capture", "paid"):
            selected.append(p)
        if len(selected) >= 2:
            break

if not selected and payments_list:
    # fallback to first items
    selected = payments_list[:2]

# 2) Get payment details for the first selected payment (if any)
if selected:
    p0 = selected[0]
    pid = p0.get("id")
    print(f"\n--- Getting Payment {pid} ---")
    p_json = do_get(f"/payments/{pid}")
    print(json.dumps(p_json, indent=2, ensure_ascii=False))
    results.append({"integration": "youkassa_get_payment", "request": {"payment_id": pid}, "response": p_json})
else:
    print("No payments found to fetch details")

# 3) Create receipts for up to 2 payments (send=False)
created_receipts = []
for p in selected[:2]:
    pid = p.get("id")
    amount = p.get("amount", {})
    value = amount.get("value", "1.00")
    currency = amount.get("currency", "RUB")

    receipt_body = {
        "payment_id": pid,
        "type": "payment",
        "send": False,
        "items": [
            {
                "description": "Test receipt from DBCV",
                "quantity": 1.0,
                "amount": {"value": str(value), "currency": currency},
                "vat_code": "2",
                "payment_mode": "full_payment",
                "payment_subject": "commodity",
            }
        ]
    }

    print(f"\n--- Creating Receipt for payment {pid} ---")
    rc = do_post("/receipts", receipt_body)
    print(json.dumps(rc, indent=2, ensure_ascii=False))

    results.append({"integration": "youkassa_create_receipt", "request": receipt_body, "response": rc})
    created_receipts.append(rc)

# Dump results to file (no credentials written)
out_path = os.path.join(os.path.dirname(__file__), "youkassa_live_results.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\nSaved live results to {out_path}")

# Print concise summary
print("\n=== Summary ===")
for r in results:
    print(f"Integration: {r['integration']}")
    print("Request:")
    print(json.dumps(r['request'], ensure_ascii=False))
    print("Response summary:")
    if isinstance(r['response'], dict):
        print(json.dumps({k: r['response'].get(k) for k in ("response", "items", "id") if k in r['response'] or k in r['response'].get('response', {})}, ensure_ascii=False, indent=2, default=str))
    else:
        print(r['response'])
    print("---")
