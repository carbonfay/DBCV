import requests


def test_yandex_weather_get_forecast(monkeypatch):
    access_key = "131ac4da-68f3-4035-9e9b-624d4a685a10"

    headers = {
        "X-Yandex-Weather-Key": access_key
    }

    captured = {}

    def fake_get(url, headers=None):
        captured["url"] = url
        captured["headers"] = headers

        class FakeResp:
            status_code = 200

            def json(self_inner):
                return {
                    "now": 1700000000,
                    "fact": {"temp": 5, "condition": "cloudy"},
                    "forecasts": [],
                }

        return FakeResp()

    monkeypatch.setattr(requests, "get", fake_get)

    response = requests.get(
        "https://api.weather.yandex.ru/v2/forecast?lat=52.37125&lon=4.89388",
        headers=headers,
    )

    assert captured.get("url") == "https://api.weather.yandex.ru/v2/forecast?lat=52.37125&lon=4.89388"
    assert captured.get("headers") and captured["headers"].get("X-Yandex-Weather-Key") == access_key

    data = response.json()
    assert "fact" in data
    assert data["fact"]["temp"] == 5
