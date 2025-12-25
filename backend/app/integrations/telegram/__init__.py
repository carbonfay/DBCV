"""Telegram интеграции.

Здесь регистрация вынесена в функцию `register_all()` чтобы избежать побочных
эффектов при импорте пакета (импорт не будет автоматически регистрировать
интеграции — регистрация выполняется явно вызовом `register_all()`).
"""

from typing import Callable


def register_all(register_func: Callable[[object], None] = None) -> None:
	"""Регистрирует все Telegram интеграции в переданном реестре.

	Args:
		register_func: функция для регистрации, принимает экземпляр интеграции.
					   Если None, будет использована `app.integrations.registry.registry.register`.
	"""
	# Импортируем конкретные интеграции локально, чтобы избежать ошибок при
	# импорте модуля, если внешние зависимости (библиотеки) отсутствуют.
	from .send_message import TelegramSendMessageIntegration
	from .send_video import TelegramSendVideoIntegration

	if register_func is None:
		from app.integrations.registry import registry

		register_func = registry.register

	# Регистрируем экземпляры интеграций
	register_func(TelegramSendMessageIntegration())
	register_func(TelegramSendVideoIntegration())


__all__ = ["register_all"]

