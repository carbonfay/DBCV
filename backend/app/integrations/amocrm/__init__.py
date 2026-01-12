"""
AmoCRM action-style integrations.
"""

from __future__ import annotations

from app.integrations.action_registry import register_action_integration

from .get_contact import AmoCRMGetContactIntegration

register_action_integration(AmoCRMGetContactIntegration)

