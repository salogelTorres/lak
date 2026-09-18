from __future__ import annotations

import logging

import httpx

from app.tools._html import HEADERS
from app.tools.base import Tool

logger = logging.getLogger(__name__)

# Open-Meteo: free, no API key, no rate-limit key required for this volume
# of use. Geocoding turns a place name into coordinates; forecast then
# needs those coordinates, not the name.
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# https://open-meteo.com/en/docs#weathervariables — WMO weather codes.
_WEATHER_DESCRIPTIONS = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "freezing fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    61: "slight rain",
    63: "moderate rain",
    65: "heavy rain",
    71: "slight snow",
    73: "moderate snow",
    75: "heavy snow",
    80: "slight rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    95: "thunderstorm",
    96: "thunderstorm with slight hail",
    99: "thunderstorm with heavy hail",
}


def get_weather(location: str) -> str:
    """Look up the current weather for `location` via Open-Meteo.

    Errors — no matching place, network failure, an incomplete response —
    are never raised; they turn into a message telling the model the lookup
    didn't work, same philosophy as the other tools.
    """
    location = location.strip()
    if not location:
        return "No location was given."

    try:
        with httpx.Client(timeout=10.0, headers=HEADERS) as client:
            geo_response = client.get(GEOCODING_URL, params={"name": location, "count": 1})
            geo_response.raise_for_status()
            results = geo_response.json().get("results") or []
            if not results:
                return f"Could not find a location matching {location!r}."

            place = results[0]
            label = ", ".join(part for part in (place.get("name"), place.get("admin1"), place.get("country")) if part)

            forecast_response = client.get(
                FORECAST_URL,
                params={
                    "latitude": place["latitude"],
                    "longitude": place["longitude"],
                    "current": "temperature_2m,weather_code,wind_speed_10m",
                },
            )
            forecast_response.raise_for_status()
            current = forecast_response.json().get("current") or {}
    except httpx.HTTPError:
        logger.warning("Weather lookup for %r failed", location, exc_info=True)
        return f"Could not fetch weather for {location!r}. The service may be unreachable."

    if "temperature_2m" not in current:
        return f"Weather data for {label} was incomplete."

    description = _WEATHER_DESCRIPTIONS.get(current.get("weather_code"), "unknown conditions")
    return (
        f"Current weather in {label}: {current['temperature_2m']}°C, {description}, "
        f"wind {current.get('wind_speed_10m', 'unknown')} km/h."
    )


TOOL = Tool(
    name="get_weather",
    description="Get the current weather for a place. Use it whenever the user asks about current weather.",
    parameters={
        "type": "object",
        "required": ["location"],
        "properties": {
            "location": {"type": "string", "description": "A city or place name, e.g. 'Madrid' or 'Paris, France'."}
        },
    },
    execute=get_weather,
)
