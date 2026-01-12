from __future__ import annotations

from typing import Any

from app.integrations.amocrm.get_contact import AmoCRMGetContactIntegration
from app.integrations.paypal.create_payout import PayPalCreatePayoutIntegration
from app.integrations.yookassa.get_payment_list import YooKassaGetPaymentListIntegration
from app.integrations.base_integration import BaseIntegration, IntegrationMetadata


def get_action_integrations() -> list[type[BaseIntegration]]:
    """
    Central place to register action-style integrations (execute/config-schema).
    """

    return [
        AmoCRMGetContactIntegration,
        PayPalCreatePayoutIntegration,
        YooKassaGetPaymentListIntegration,
    ]


def get_action_integrations_metadata() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for cls in get_action_integrations():
        md: IntegrationMetadata = cls.metadata
        items.append(md.to_dict())
    return items


def get_action_integration_by_id(integration_id: str) -> type[BaseIntegration] | None:
    for cls in get_action_integrations():
        if cls.metadata.id == integration_id:
            return cls
    return None


