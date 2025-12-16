from .get_uv_index import OpenWeatherMapGetUVIndexIntegration
from app.integrations.registry import registry

try:
	registry.register(OpenWeatherMapGetUVIndexIntegration())
except Exception:
	# Registration should never break import-time behavior
	pass

