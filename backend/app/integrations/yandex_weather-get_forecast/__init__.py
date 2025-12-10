"""Deprecated package shim.

This package was renamed to `yandex_weather_get_forecast`. Importing
from the old package will raise an ImportError to avoid duplicate
registrations.
"""

raise ImportError("yandex_weather-get_forecast package is deprecated. Use app.integrations.yandex_weather_get_forecast instead")
