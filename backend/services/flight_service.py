"""Amadeus API wrapper for flight search."""
import os
from dataclasses import dataclass
from datetime import date
from typing import Optional
import httpx
import redis
import json


@dataclass
class FlightOption:
    id: str
    origin: str
    destination: str
    departure: str
    arrival: str
    duration: str
    price: float
    currency: str
    airline: str
    stops: int
    cabin_class: str = "ECONOMY"


_TOKEN_KEY = "amadeus:access_token"


async def _get_amadeus_token(redis_client: Optional[redis.Redis] = None) -> str:
    if redis_client:
        cached = redis_client.get(_TOKEN_KEY)
        if cached:
            return cached.decode()

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://test.api.amadeus.com/v1/security/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": os.getenv("AMADEUS_API_KEY", ""),
                "client_secret": os.getenv("AMADEUS_API_SECRET", ""),
            },
        )
        resp.raise_for_status()
        data = resp.json()
        token = data["access_token"]
        expires_in = data.get("expires_in", 1799)

        if redis_client:
            redis_client.setex(_TOKEN_KEY, expires_in - 60, token)
        return token


async def search_flights(
    origin: str,
    destination: str,
    departure_date: date,
    adults: int = 1,
    max_price: Optional[float] = None,
    redis_client: Optional[redis.Redis] = None,
) -> list[FlightOption]:
    cache_key = f"flights:{origin}:{destination}:{departure_date}:{adults}"
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            raw = json.loads(cached)
            return [FlightOption(**f) for f in raw]

    try:
        token = await _get_amadeus_token(redis_client)
    except Exception:
        return _mock_flights(origin, destination, departure_date)
    params = {
        "originLocationCode": origin,
        "destinationLocationCode": destination,
        "departureDate": str(departure_date),
        "adults": adults,
        "max": 5,
        "currencyCode": "USD",
    }
    if max_price:
        params["maxPrice"] = int(max_price)

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://test.api.amadeus.com/v2/shopping/flight-offers",
            params=params,
            headers={"Authorization": f"Bearer {token}"},
            timeout=15.0,
        )
        if resp.status_code != 200:
            return _mock_flights(origin, destination, departure_date)
        data = resp.json()

    options: list[FlightOption] = []
    for offer in data.get("data", [])[:3]:
        itinerary = offer["itineraries"][0]
        segment = itinerary["segments"][0]
        price = float(offer["price"]["grandTotal"])
        options.append(
            FlightOption(
                id=offer["id"],
                origin=origin,
                destination=destination,
                departure=segment["departure"]["at"],
                arrival=segment["arrival"]["at"],
                duration=itinerary["duration"],
                price=price,
                currency=offer["price"]["currency"],
                airline=segment["carrierCode"],
                stops=len(itinerary["segments"]) - 1,
            )
        )

    if redis_client and options:
        redis_client.setex(cache_key, 600, json.dumps([o.__dict__ for o in options]))
    return options


def _mock_flights(origin: str, destination: str, dep: date) -> list[FlightOption]:
    return [
        FlightOption(
            id="MOCK-1",
            origin=origin,
            destination=destination,
            departure=f"{dep}T08:00:00",
            arrival=f"{dep}T11:30:00",
            duration="PT3H30M",
            price=350.0,
            currency="USD",
            airline="AA",
            stops=0,
        ),
        FlightOption(
            id="MOCK-2",
            origin=origin,
            destination=destination,
            departure=f"{dep}T14:00:00",
            arrival=f"{dep}T19:45:00",
            duration="PT5H45M",
            price=250.0,
            currency="USD",
            airline="UA",
            stops=1,
        ),
    ]
