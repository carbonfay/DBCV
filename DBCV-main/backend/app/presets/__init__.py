"""Модуль presets для создания типовых шагов."""
from app.presets.registry import registry, PresetRegistry
from app.presets.base import BasePreset, PresetMetadata
from app.presets.conditional import IfPreset

# Регистрируем все presets
if_preset = IfPreset()
registry.register(if_preset)

__all__ = [
    "registry",
    "PresetRegistry",
    "BasePreset",
    "PresetMetadata",
    "IfPreset",
]

