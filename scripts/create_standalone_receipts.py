"""Create two standalone YooKassa receipts (send=False).

Usage (PowerShell):
  $env:YOOKASSA_SHOP_ID='1236220'; $env:YOOKASSA_API_KEY='test_...'; python scripts/create_standalone_receipts.py

Notes:
- Uses only Python stdlib. Does not install SDK.
- Creates two receipts with `send=False` and unique external IDs.
"""
import os
import json
import time
import uuid
from typing import Any, Dict, List
from urllib import request, parse, error

API_BASE = "https://api.yookassa.ru/v3"

SHOP_ID = os.environ.get("YOOKASSA_SHOP_ID")
API_KEY = os.environ.get("YOOKASSA_API_KEY")

if not SHOP_ID or not API_KEY:
    raise SystemExit("YOOKASSA_SHOP_ID and YOOKASSA_API_KEY must be set as environment variables")

import base64
BASIC_AUTH = base64.b64encode(f"{SHOP_ID}:{API_KEY}".encode()).decode()
HEADERS = {"Accept": "application/json", "Content-Type": "application/json", "Authorization": f"Basic {BASIC_AUTH}"}


def do_post(path: str, body: Dict[str, Any], idempotence_key: str = None):
    url = f"{API_BASE}{path}"
    data = json.dumps(body).encode()
    headers = dict(HEADERS)
    if idempotence_key:
        headers["Idempotence-Key"] = idempotence_key
    req = request.Request(url, data=data, headers=headers, method="POST")
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


results: List[Dict[str, Any]] = []

for i in range(2):
    external_id = f"dbcv-test-{int(time.time())}-{i}-{uuid.uuid4().hex[:6]}"
    receipt_body = {
        "type": "sell",
        "external_id": external_id,
        "send": False,
        "items": [
            {
                "description": "Test standalone receipt from DBCV",
                "quantity": 1.0,
                "amount": {"value": "1.00", "currency": "RUB"},
                "vat_code": "2",
                "payment_mode": "full_payment",
                "payment_subject": "commodity",
            }
        ],
        # Minimal required fields to satisfy API validation for standalone receipts
        "settlements": [
            {"type": "bank_card", "amount": {"value": "1.00", "currency": "RUB"}}
        ],
        "customer": {"phone": "+79000000000"}
    }

    print(f"\n--- Creating standalone receipt {external_id} (send=False) ---")
    id_key = uuid.uuid4().hex
    rc = do_post("/receipts", receipt_body, idempotence_key=id_key)
    print(json.dumps(rc, indent=2, ensure_ascii=False))
    results.append({"external_id": external_id, "idempotence_key": id_key, "response": rc})

out_path = os.path.join(os.path.dirname(__file__), "youkassa_create_standalone_results.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\nSaved results to {out_path}")
