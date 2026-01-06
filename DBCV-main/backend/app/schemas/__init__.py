from __future__ import annotations

from collections.abc import Callable
from importlib import import_module

_MODEL_MODULES = [
    "app.schemas.base",
    "app.schemas.block",
    "app.schemas.subscriber",
    "app.schemas.variables",
    "app.schemas.anonymous_user",
    "app.schemas.user",
    "app.schemas.bot",
    "app.schemas.channel",
    "app.schemas.step",
    "app.schemas.message",
    "app.schemas.attachment",
    "app.schemas.request",
    "app.schemas.connection",
    "app.schemas.templates",
    "app.schemas.template_group",
    "app.schemas.emitter",
    "app.schemas.cron",
    "app.schemas.widget",
    "app.schemas.note",
    "app.schemas.credentials",
    "app.schemas.session",
]

_model_rebuilders: list[Callable[[], None]] = []


def register_model_rebuilder(func: Callable[[], None]) -> None:
    _model_rebuilders.append(func)


def rebuild_models() -> None:
    imported_modules = [import_module(module_path) for module_path in _MODEL_MODULES]

    types_namespace: dict[str, type] = {}
    for module in imported_modules:
        for name, value in module.__dict__.items():
            if isinstance(value, type):
                types_namespace.setdefault(name, value)

    for module in imported_modules:
        for name, value in types_namespace.items():
            module.__dict__.setdefault(name, value)

    for func in _model_rebuilders:
        func()


__all__ = ["register_model_rebuilder", "rebuild_models"]
