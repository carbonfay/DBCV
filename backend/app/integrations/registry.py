from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter

from app.integrations.example_integration.integration import ExampleIntegration

if TYPE_CHECKING:  # pragma: no cover
    from aiogram import Router as AiogramRouter

from app.integrations.base import Integration


def get_integrations() -> list[Integration]:
    """
    Central place to register integrations.

    Later we can switch to dynamic discovery (entrypoints/importlib),
    but explicit list is simplest and stable.
    """

    return [
        ExampleIntegration(),
    ]


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



