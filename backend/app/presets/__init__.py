"""Presets интеграции."""
from .loop import LoopPreset
from .parallel import ParallelPreset
from app.presets.registry import registry

# Автоматическая регистрация пресетов
registry.register(LoopPreset())
registry.register(ParallelPreset())