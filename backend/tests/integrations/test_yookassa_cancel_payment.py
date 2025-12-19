import pytest
from app.integrations.yookassa.cancel_payment import YooKassaCancelPaymentIntegration


@pytest.mark.unit
def test_yookassa_cancel_payment_metadata_basic():
    integration = YooKassaCancelPaymentIntegration()
    meta = integration.metadata

    assert meta.id == "yookassa.cancel_payment"
    assert meta.version == "1.0.0"
    assert isinstance(meta.name, str) and meta.name.strip()
    assert isinstance(meta.description, str) and meta.description.strip()

    schema = meta.config_schema
    assert schema["type"] == "object"
    assert "payment_id" in schema.get("required", [])
    assert "properties" in schema
    assert schema["properties"]["payment_id"]["type"] == "string"
