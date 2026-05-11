"""OpenWeather API wrapper for forecasts and alerts."""
import os
from dataclasses import dataclass
from datetime import date
from typing import Optional
import httpx


@dataclass
class WeatherForecast:
    date: str
    city: str
    temp_min: float
    temp_max: float
    description: str
    icon: str
    humidity: int
    wind_speed: float
    alert: Optional[str] = None


async def get_forecast(city: str, target_date: date) -> WeatherForecast:
    api_key = os.getenv("OPENWEATHER_API_KEY", "")
    if not api_key:
        return _mock_forecast(city, target_date)

    async with httpx.AsyncClient() as client:
        geo_resp = await client.get(
            "https://api.openweathermap.org/geo/1.0/direct",
            params={"q": city, "limit": 1, "appid": api_key},
            timeout=10.0,
        )
        if geo_resp.status_code != 200 or not geo_resp.json():
            return _mock_forecast(city, target_date)

        geo = geo_resp.json()[0]
        forecast_resp = await client.get(
            "https://api.openweathermap.org/data/2.5/forecast",
            params={"lat": geo["lat"], "lon": geo["lon"], "appid": api_key, "units": "metric"},
            timeout=10.0,
        )
        if forecast_resp.status_code != 200:
            return _mock_forecast(city, target_date)

        data = forecast_resp.json()

    target_str = str(target_date)
    day_forecasts = [
        item for item in data.get("list", [])
        if item["dt_txt"].startswith(target_str)
    ]
    if not day_forecasts:
        return _mock_forecast(city, target_date)

    temps = [f["main"]["temp"] for f in day_forecasts]
    main = day_forecasts[len(day_forecasts) // 2]
    alert = None
    weather_main = main["weather"][0]["main"]
    if weather_main in ("Thunderstorm", "Tornado", "Hurricane"):
        alert = f"Severe weather warning: {weather_main} expected on {target_date}"

    return WeatherForecast(
        date=target_str,
        city=city,
        temp_min=min(temps),
        temp_max=max(temps),
        description=main["weather"][0]["description"],
        icon=main["weather"][0]["icon"],
        humidity=main["main"]["humidity"],
        wind_speed=main["wind"]["speed"],
        alert=alert,
    )


async def get_weather_alerts(city: str, dates: list[date]) -> list[str]:
    alerts: list[str] = []
    for d in dates:
        forecast = await get_forecast(city, d)
        if forecast.alert:
            alerts.append(forecast.alert)
    return alerts


def _mock_forecast(city: str, target_date: date) -> WeatherForecast:
    return WeatherForecast(
        date=str(target_date),
        city=city,
        temp_min=18.0,
        temp_max=26.0,
        description="partly cloudy",
        icon="02d",
        humidity=65,
        wind_speed=3.5,
    )
