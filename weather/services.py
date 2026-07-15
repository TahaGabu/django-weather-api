"""
Third-party integrations: OpenWeatherMap + optional OpenAI advice.
Falls back to deterministic demo/rules when keys are missing so the portfolio still runs.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

import requests
from django.conf import settings
from django.core.cache import cache


class WeatherAPIError(Exception):
    pass


DEMO_CITIES = {
    "london": {
        "name": "London",
        "country": "GB",
        "temp": 14.2,
        "feels_like": 12.8,
        "humidity": 72,
        "wind_speed": 4.1,
        "condition": "Broken clouds",
        "icon": "04d",
        "forecast": [
            {"day": "Thu", "temp": 15, "condition": "Clouds", "icon": "03d"},
            {"day": "Fri", "temp": 17, "condition": "Clear", "icon": "01d"},
            {"day": "Sat", "temp": 13, "condition": "Rain", "icon": "10d"},
            {"day": "Sun", "temp": 12, "condition": "Rain", "icon": "09d"},
            {"day": "Mon", "temp": 16, "condition": "Clouds", "icon": "02d"},
        ],
    },
    "mumbai": {
        "name": "Mumbai",
        "country": "IN",
        "temp": 31.5,
        "feels_like": 36.0,
        "humidity": 78,
        "wind_speed": 3.2,
        "condition": "Haze",
        "icon": "50d",
        "forecast": [
            {"day": "Thu", "temp": 32, "condition": "Haze", "icon": "50d"},
            {"day": "Fri", "temp": 33, "condition": "Clouds", "icon": "02d"},
            {"day": "Sat", "temp": 30, "condition": "Rain", "icon": "10d"},
            {"day": "Sun", "temp": 29, "condition": "Rain", "icon": "09d"},
            {"day": "Mon", "temp": 31, "condition": "Clear", "icon": "01d"},
        ],
    },
    "tokyo": {
        "name": "Tokyo",
        "country": "JP",
        "temp": 22.0,
        "feels_like": 21.4,
        "humidity": 55,
        "wind_speed": 2.8,
        "condition": "Clear sky",
        "icon": "01d",
        "forecast": [
            {"day": "Thu", "temp": 23, "condition": "Clear", "icon": "01d"},
            {"day": "Fri", "temp": 24, "condition": "Clouds", "icon": "02d"},
            {"day": "Sat", "temp": 21, "condition": "Rain", "icon": "10d"},
            {"day": "Sun", "temp": 20, "condition": "Clouds", "icon": "03d"},
            {"day": "Mon", "temp": 22, "condition": "Clear", "icon": "01d"},
        ],
    },
    "new york": {
        "name": "New York",
        "country": "US",
        "temp": 18.6,
        "feels_like": 17.9,
        "humidity": 61,
        "wind_speed": 5.4,
        "condition": "Few clouds",
        "icon": "02d",
        "forecast": [
            {"day": "Thu", "temp": 19, "condition": "Clouds", "icon": "02d"},
            {"day": "Fri", "temp": 21, "condition": "Clear", "icon": "01d"},
            {"day": "Sat", "temp": 17, "condition": "Rain", "icon": "10d"},
            {"day": "Sun", "temp": 16, "condition": "Clouds", "icon": "04d"},
            {"day": "Mon", "temp": 20, "condition": "Clear", "icon": "01d"},
        ],
    },
}


def _cache_key(prefix: str, city: str) -> str:
    digest = hashlib.sha256(city.strip().lower().encode()).hexdigest()[:24]
    return f"skycast:{prefix}:{digest}"


def _demo_payload(city: str) -> dict[str, Any]:
    key = city.strip().lower()
    base = DEMO_CITIES.get(key) or {
        "name": city.title(),
        "country": "XX",
        "temp": 20.0,
        "feels_like": 19.5,
        "humidity": 60,
        "wind_speed": 3.0,
        "condition": "Partly cloudy",
        "icon": "02d",
        "forecast": [
            {"day": "Thu", "temp": 21, "condition": "Clouds", "icon": "03d"},
            {"day": "Fri", "temp": 22, "condition": "Clear", "icon": "01d"},
            {"day": "Sat", "temp": 19, "condition": "Rain", "icon": "10d"},
            {"day": "Sun", "temp": 18, "condition": "Clouds", "icon": "04d"},
            {"day": "Mon", "temp": 20, "condition": "Clear", "icon": "01d"},
        ],
    }
    return {
        "city": base["name"],
        "country": base["country"],
        "temp": base["temp"],
        "feels_like": base["feels_like"],
        "humidity": base["humidity"],
        "wind_speed": base["wind_speed"],
        "condition": base["condition"],
        "icon": base["icon"],
        "icon_url": f"https://openweathermap.org/img/wn/{base['icon']}@2x.png",
        "forecast": base["forecast"],
        "source": "demo",
        "demo_note": "Showing demo data — add OPENWEATHER_API_KEY for live API results.",
    }


def fetch_weather(city: str) -> dict[str, Any]:
    city = (city or "").strip()
    if not city:
        raise WeatherAPIError("City is required.")

    cache_key = _cache_key("weather", city)
    cached = cache.get(cache_key)
    if cached:
        payload = dict(cached)
        payload["source"] = "cache"
        return payload

    api_key = settings.OPENWEATHER_API_KEY
    if not api_key:
        payload = _demo_payload(city)
        cache.set(cache_key, payload, settings.WEATHER_CACHE_SECONDS)
        return payload

    params = {"q": city, "appid": api_key, "units": "metric"}
    try:
        current = requests.get(
            f"{settings.OPENWEATHER_BASE_URL}/weather",
            params=params,
            timeout=10,
        )
        if current.status_code == 404:
            raise WeatherAPIError(f"City not found: {city}")
        current.raise_for_status()
        cdata = current.json()

        forecast_resp = requests.get(
            f"{settings.OPENWEATHER_BASE_URL}/forecast",
            params=params,
            timeout=10,
        )
        forecast_resp.raise_for_status()
        fdata = forecast_resp.json()
    except requests.RequestException as exc:
        raise WeatherAPIError(f"OpenWeather request failed: {exc}") from exc

    weather0 = (cdata.get("weather") or [{}])[0]
    icon = weather0.get("icon", "01d")
    # Take one slot per day around midday from 3-hour forecast
    day_map: dict[str, dict] = {}
    for item in fdata.get("list", []):
        dt_txt = item.get("dt_txt", "")
        day = dt_txt[:10]
        hour = dt_txt[11:13]
        if day not in day_map or hour == "12":
            w = (item.get("weather") or [{}])[0]
            day_map[day] = {
                "day": day,
                "temp": round(item.get("main", {}).get("temp", 0), 1),
                "condition": w.get("main", ""),
                "icon": w.get("icon", "01d"),
            }
        if len(day_map) >= 5:
            break

    payload = {
        "city": cdata.get("name") or city,
        "country": (cdata.get("sys") or {}).get("country", ""),
        "temp": round((cdata.get("main") or {}).get("temp", 0), 1),
        "feels_like": round((cdata.get("main") or {}).get("feels_like", 0), 1),
        "humidity": (cdata.get("main") or {}).get("humidity", 0),
        "wind_speed": (cdata.get("wind") or {}).get("speed", 0),
        "condition": weather0.get("description", "").title(),
        "icon": icon,
        "icon_url": f"https://openweathermap.org/img/wn/{icon}@2x.png",
        "forecast": list(day_map.values()),
        "source": "openweather",
        "demo_note": "",
    }
    cache.set(cache_key, payload, settings.WEATHER_CACHE_SECONDS)
    return payload


def rules_based_advice(weather: dict[str, Any]) -> str:
    temp = float(weather.get("temp") or 0)
    condition = (weather.get("condition") or "").lower()
    humidity = int(weather.get("humidity") or 0)
    tips = []

    if temp >= 32:
        tips.append("Heat stress risk is elevated — plan shaded breaks and hydrate often.")
    elif temp >= 24:
        tips.append("Warm day: light layers work well for outdoor errands.")
    elif temp <= 5:
        tips.append("Cold air: layered clothing and covered extremities are safer.")
    else:
        tips.append("Mild temperatures — a light jacket handles most of the day.")

    if any(k in condition for k in ("rain", "drizzle", "thunder")):
        tips.append("Precipitation likely: pack a compact umbrella and waterproof footwear.")
    elif "snow" in condition:
        tips.append("Snow conditions: allow extra commute time and use high-traction shoes.")
    elif "clear" in condition:
        tips.append("Clear skies: UV exposure can still be high — sunscreen helps midday.")

    if humidity >= 75:
        tips.append("High humidity: choose breathable fabrics and ease intense outdoor workouts.")
    if float(weather.get("wind_speed") or 0) >= 8:
        tips.append("Gusty winds: secure loose outdoor items and bike carefully.")

    city = weather.get("city", "your city")
    return f"Skycast advisor for {city}: " + " ".join(tips)


def openai_advice(weather: dict[str, Any]) -> str | None:
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        return None

    prompt = (
        "Give 2-3 short, practical outdoor tips (max 80 words) for this weather. "
        "No markdown, no disclaimer.\n"
        f"{json.dumps({k: weather[k] for k in ('city','country','temp','feels_like','humidity','wind_speed','condition') if k in weather})}"
    )
    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a concise weather lifestyle advisor."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.6,
                "max_tokens": 160,
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except (requests.RequestException, KeyError, IndexError, TypeError):
        return None


def generate_advice(weather: dict[str, Any]) -> tuple[str, str]:
    """Returns (advice_text, mode) where mode is openai|rules."""
    ai = openai_advice(weather)
    if ai:
        return ai, "openai"
    return rules_based_advice(weather), "rules"
