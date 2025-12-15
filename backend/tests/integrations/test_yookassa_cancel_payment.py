import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.integrations.yookassa.cancel_payment import (
    YooKassaCancelPaymentIntegration,
)


def test_yookassa_cancel_payment_metadata_basic():
    integration = YooKassaCancelPaymentIntegration()
    meta = integration.metadata

    assert meta.id == "yookassa.cancel_payment"

    assert meta.version == "1.0.0"

    assert isinstance(meta.name, str) and meta.name
    assert isinstance(meta.description, str) and meta.description

    assert meta.category == "payments"
    assert isinstance(meta.icon_s3_key, str) and meta.icon_s3_key
    assert isinstance(meta.color, str) and meta.color.startswith("#")

    schema = meta.config_schema
    assert schema["type"] == "object"
    assert "payment_id" in schema.get("required", [])
    assert "properties" in schema
    props = schema["properties"]
    assert "payment_id" in props
    assert props["payment_id"]["type"] == "string"
