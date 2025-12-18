import pytest
from app.integrations.yookassa.refund import YooKassaRefundIntegration


@pytest.mark.unit
def test_yookassa_refund_metadata_basic():
    integration = YooKassaRefundIntegration()
    meta = integration.metadata

    assert meta.id == "yookassa.refund"
    assert meta.version == "1.0.0"
    assert isinstance(meta.name, str) and meta.name.strip()
    assert isinstance(meta.description, str) and meta.description.strip()

    schema = meta.config_schema
    assert schema["type"] == "object"
    assert "payment_id" in schema.get("required", [])
    assert "amount" in schema.get("required", [])
    assert "properties" in schema
    assert schema["properties"]["payment_id"]["type"] == "string"
    assert schema["properties"]["amount"]["type"] == "number"
