#!/usr/bin/env python3
"""Quick script to get payment_id from YooKassa."""

import http.client
import json
import base64
import uuid

shop_id = "1236220"
secret_key = "test_PWG4RiNh9nJg-e8bsvBLkiXBzogbg9vXIKIMyfcHgZU"

body = {
    "amount": {"value": "10.00", "currency": "RUB"},
    "confirmation": {"type": "redirect", "return_url": "https://example.com/return"},
    "capture": True,
    "description": "Test",
}

headers = {
    "Authorization": "Basic " + base64.b64encode(f"{shop_id}:{secret_key}".encode()).decode(),
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Idempotence-Key": str(uuid.uuid4()),
}

print("Sending request to YooKassa...")
print(f"Idempotence-Key: {headers['Idempotence-Key']}")

conn = http.client.HTTPSConnection("api.yookassa.ru", 443, timeout=30)
try:
    conn.request("POST", "/v3/payments", body=json.dumps(body).encode(), headers=headers)
    resp = conn.getresponse()
    data = resp.read().decode()
    print(f"Status: {resp.status}")
    print(f"Response:\n{data}")
    
    if resp.status == 200:
        parsed = json.loads(data)
        payment_id = parsed.get("id")
        print(f"\n✓ Payment ID: {payment_id}")
        print(f"Use this payment_id in create_receipt")
finally:
    conn.close()
