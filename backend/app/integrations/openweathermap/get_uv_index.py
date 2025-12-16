"""OpenWeatherMap Get UV Index integration using `httpx` (recommended in SAFE_LIBRARIES.md).

This integration expects `config` to contain `lat` and `lon` (numbers or strings).
Credentials are resolved via `credentials_resolver.get_default_for(..., provider="openweathermap", strategy="api_key")`
and should contain the API key under `payload['api_key']` (or `api_key` at root).
"""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Try to import httpx as recommended by SAFE_LIBRARIES.md
try:
	import httpx
	HTTPX_AVAILABLE = True
except Exception:
	httpx = None  # type: ignore
	HTTPX_AVAILABLE = False


class OpenWeatherMapGetUVIndexIntegration(BaseIntegration):
	"""Get UV Index from OpenWeatherMap using direct HTTP requests via httpx."""

	@property
	def metadata(self) -> IntegrationMetadata:
		return IntegrationMetadata(
			id="openweathermap_get_uv_index",
			version="1.0.0",
			name="OpenWeatherMap Get UV Index",
			description="Получение UV индекса с OpenWeatherMap по координатам (lat/lon)",
			category="weather",
			icon_s3_key="icons/integrations/openweathermap.svg",
			color="#00aaff",
			config_schema={
				"type": "object",
				"required": ["lat", "lon"],
				"properties": {
					"lat": {"type": ["number", "string"], "title": "Latitude"},
					"lon": {"type": ["number", "string"], "title": "Longitude"}
				}
			},
			credentials_provider="openweathermap",
			credentials_strategy="api_key",
			library_name="httpx>=0.27.0" if HTTPX_AVAILABLE else None,
			examples=[
				{
					"title": "Get UV Index",
					"config": {"lat": 55.75, "lon": 37.6167}
				}
			]
		)

	async def execute(
		self,
		config: Dict[str, Any],
		credentials_resolver: CredentialsResolver,
		bot_id: UUID,
		logger: BotLogger,
	) -> Dict[str, Any]:
		if not HTTPX_AVAILABLE:
			await logger.error("httpx library is not available")
			return {
				"response": {
					"ok": False,
					"error_code": 500,
					"description": "httpx library is not installed"
				}
			}

		# Resolve credentials
		creds = await credentials_resolver.get_default_for(
			bot_id=bot_id,
			provider="openweathermap",
			strategy="api_key",
		)

		if not creds:
			await logger.error("OpenWeatherMap credentials not found")
			return {
				"response": {
					"ok": False,
					"error_code": 401,
					"description": "OpenWeatherMap API key not found in credentials"
				}
			}

		# Credentials payload handling (support payload wrapper or flat dict)
		payload = creds.get("payload", {}) if isinstance(creds, dict) else {}
		if not payload:
			payload = creds

		api_key = None
		if isinstance(payload, dict):
			api_key = payload.get("api_key") or payload.get("key") or payload.get("token")

		if not api_key:
			await logger.error(f"OpenWeatherMap api_key not found in credentials. Available keys: {list(payload.keys()) if isinstance(payload, dict) else []}")
			return {
				"response": {
					"ok": False,
					"error_code": 401,
					"description": "api_key not found in credentials"
				}
			}

		# Validate config
		lat = config.get("lat")
		lon = config.get("lon")
		if lat is None or lon is None:
			await logger.error("lat and lon are required in config")
			return {
				"response": {
					"ok": False,
					"error_code": 400,
					"description": "lat and lon are required in config"
				}
			}

		# Build request
		try:
			lat_str = str(lat)
			lon_str = str(lon)
			url = f"https://api.openweathermap.org/data/2.5/uvi?lat={lat_str}&lon={lon_str}&appid={api_key}"

			async with httpx.AsyncClient(timeout=10.0) as client:
				resp = await client.get(url)

			if resp.status_code == 200:
				data = resp.json()
				return {"response": {"ok": True, "result": data}}

			# Non-200 response
			await logger.error(f"OpenWeatherMap returned status {resp.status_code}: {resp.text}")
			return {
				"response": {
					"ok": False,
					"error_code": resp.status_code,
					"description": resp.text
				}
			}

		except httpx.RequestError as e:
			await logger.error(f"HTTP request error: {e}")
			return {
				"response": {
					"ok": False,
					"error_code": 502,
					"description": str(e)
				}
			}
		except Exception as e:
			await logger.error(f"Unexpected error: {e}")
			return {
				"response": {
					"ok": False,
					"error_code": 500,
					"description": str(e)
				}
			}

