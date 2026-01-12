from __future__ import annotations

import importlib
import pkgutil
from typing import TYPE_CHECKING

from fastapi import APIRouter

if TYPE_CHECKING:  # pragma: no cover
    from aiogram import Router as AiogramRouter

from app.integrations.base import Integration


_PLATFORM_INTEGRATION_CLASSES: list[type[Integration]] = []
_DISCOVERED: bool = False


def register_platform_integration(cls: type[Integration]) -> None:
    """
    Called by `app.integrations.{service}.__init__` to register platform integrations.

    Keeping registration close to the service package makes it easy to add/remove
    integrations without editing a central list.
    """

    if cls not in _PLATFORM_INTEGRATION_CLASSES:
        _PLATFORM_INTEGRATION_CLASSES.append(cls)


def _ensure_discovered() -> None:
    """
    Import all integration service packages once so their `__init__.py` runs and
    registers integrations via `register_platform_integration`.
    """

    global _DISCOVERED
    if _DISCOVERED:
        return

    integrations_pkg = importlib.import_module("app.integrations")
    for m in pkgutil.iter_modules(integrations_pkg.__path__):
        if m.ispkg:
            importlib.import_module(f"{integrations_pkg.__name__}.{m.name}")

    _DISCOVERED = True


def get_integrations() -> list[Integration]:
    """
    Central place to access platform integrations.

    Registration happens inside `backend/app/integrations/{service}/__init__.py`.
    """

    _ensure_discovered()
    return [cls() for cls in _PLATFORM_INTEGRATION_CLASSES]


def get_integration_routers() -> list[APIRouter]:
    routers: list[APIRouter] = []
    for i in get_integrations():
        r = i.get_api_router()
        if r is not None:
            routers.append(r)
    return routers


def get_integration_bot_routers() -> list["AiogramRouter"]:
    routers: list["AiogramRouter"] = []
    for i in get_integrations():
        r = i.get_bot_router()
        if r is not None:
            routers.append(r)
    return routers



