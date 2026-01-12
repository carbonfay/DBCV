from __future__ import annotations

import importlib
import pkgutil
from typing import Any

from app.integrations.base_integration import BaseIntegration, IntegrationMetadata


_ACTION_INTEGRATION_CLASSES: list[type[BaseIntegration]] = []
_DISCOVERED: bool = False


def register_action_integration(cls: type[BaseIntegration]) -> None:
    """
    Called by `app.integrations.{service}.__init__` to register action integrations.
    """

    if cls not in _ACTION_INTEGRATION_CLASSES:
        _ACTION_INTEGRATION_CLASSES.append(cls)


def _ensure_discovered() -> None:
    """
    Import all integration service packages once so their `__init__.py` runs and
    registers action integrations via `register_action_integration`.
    """

    global _DISCOVERED
    if _DISCOVERED:
        return

    integrations_pkg = importlib.import_module("app.integrations")
    for m in pkgutil.iter_modules(integrations_pkg.__path__):
        if m.ispkg:
            importlib.import_module(f"{integrations_pkg.__name__}.{m.name}")

    _DISCOVERED = True


def get_action_integrations() -> list[type[BaseIntegration]]:
    """
    Central place to access action-style integrations (execute/config-schema).

    Registration happens inside `backend/app/integrations/{service}/__init__.py`.
    """

    _ensure_discovered()
    return list(_ACTION_INTEGRATION_CLASSES)


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


