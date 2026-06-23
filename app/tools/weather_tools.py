from typing import Any

import requests


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def get_weather(city: str) -> dict[str, Any]:
    try:
        geo_response = requests.get(
            GEOCODING_URL,
            params={"name": city, "count": 1, "language": "en", "format": "json"},
            timeout=10,
        )
        geo_response.raise_for_status()
        locations = geo_response.json().get("results", [])
        if not locations:
            return {"success": False, "error": f"No location found for '{city}'."}

        location = locations[0]
        weather_response = requests.get(
            FORECAST_URL,
            params={
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "current_weather": True,
            },
            timeout=10,
        )
        weather_response.raise_for_status()
        current_weather = weather_response.json().get("current_weather")
        if not current_weather:
            return {"success": False, "error": "Weather data was not available."}

        return {
            "success": True,
            "city": location.get("name", city),
            "country": location.get("country", ""),
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "current_weather": current_weather,
        }
    except requests.RequestException as exc:
        return {"success": False, "error": f"Weather API request failed: {exc}"}
