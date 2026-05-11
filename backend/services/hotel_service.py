"""Booking.com RapidAPI wrapper for hotel search."""
import os
import json
from dataclasses import dataclass, field
from datetime import date
from typing import Optional
import httpx
import redis


@dataclass
class HotelOption:
    id: str
    name: str
    city: str
    area: str
    price_per_night: float
    currency: str
    rating: float
    amenities: list[str] = field(default_factory=list)
    proximity_score: float = 0.0
    url: str = ""


async def search_hotels(
    city: str,
    check_in: date,
    check_out: date,
    adults: int = 1,
    max_price_per_night: Optional[float] = None,
    redis_client: Optional[redis.Redis] = None,
) -> list[HotelOption]:
    cache_key = f"hotels:{city}:{check_in}:{check_out}:{adults}"
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            raw = json.loads(cached)
            return [HotelOption(**h) for h in raw]

    api_key = os.getenv("BOOKING_API_KEY", "")
    if not api_key:
        options = _mock_hotels(city)
        return options

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "booking-com15.p.rapidapi.com",
    }
    async with httpx.AsyncClient() as client:
        # Resolve destination ID
        dest_resp = await client.get(
            "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchDestination",
            params={"query": city},
            headers=headers,
            timeout=10.0,
        )
        if dest_resp.status_code != 200:
            return _mock_hotels(city)

        dest_data = dest_resp.json()
        destinations = dest_data.get("data", [])
        if not destinations:
            return _mock_hotels(city)

        dest_id = destinations[0]["dest_id"]
        dest_type = destinations[0]["dest_type"]

        hotel_resp = await client.get(
            "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchHotels",
            params={
                "dest_id": dest_id,
                "search_type": dest_type,
                "arrival_date": str(check_in),
                "departure_date": str(check_out),
                "adults": adults,
                "room_qty": 1,
                "page_number": 1,
                "units": "metric",
                "temperature_unit": "c",
                "languagecode": "en-us",
                "currency_code": "USD",
            },
            headers=headers,
            timeout=15.0,
        )
        if hotel_resp.status_code != 200:
            return _mock_hotels(city)

        data = hotel_resp.json()

    options: list[HotelOption] = []
    for hotel in data.get("data", {}).get("hotels", [])[:3]:
        price = float(hotel.get("property", {}).get("priceBreakdown", {}).get("grossPrice", {}).get("value", 0))
        if max_price_per_night and price > max_price_per_night:
            continue
        options.append(
            HotelOption(
                id=str(hotel.get("hotel_id", "")),
                name=hotel.get("property", {}).get("name", "Unknown"),
                city=city,
                area=hotel.get("property", {}).get("wishlistName", city),
                price_per_night=price,
                currency="USD",
                rating=float(hotel.get("property", {}).get("reviewScore", 0)),
                amenities=[],
                proximity_score=float(hotel.get("property", {}).get("reviewScoreWord", {}) if isinstance(hotel.get("property", {}).get("reviewScoreWord"), (int, float)) else 0),
            )
        )

    if not options:
        options = _mock_hotels(city)

    if redis_client:
        redis_client.setex(cache_key, 600, json.dumps([o.__dict__ for o in options]))
    return options


def _mock_hotels(city: str) -> list[HotelOption]:
    return [
        HotelOption(
            id="MOCK-H1",
            name=f"Grand {city} Hotel",
            city=city,
            area="City Center",
            price_per_night=150.0,
            currency="USD",
            rating=8.5,
            amenities=["WiFi", "Breakfast", "Pool"],
            proximity_score=9.0,
        ),
        HotelOption(
            id="MOCK-H2",
            name=f"{city} Budget Inn",
            city=city,
            area="Old Town",
            price_per_night=75.0,
            currency="USD",
            rating=7.2,
            amenities=["WiFi"],
            proximity_score=7.5,
        ),
        HotelOption(
            id="MOCK-H3",
            name=f"Luxury {city} Suites",
            city=city,
            area="Waterfront",
            price_per_night=280.0,
            currency="USD",
            rating=9.1,
            amenities=["WiFi", "Spa", "Gym", "Pool", "Breakfast"],
            proximity_score=8.0,
        ),
    ]
