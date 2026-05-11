"""Google Maps API wrapper for attractions and places."""
import os
from dataclasses import dataclass, field
from typing import Optional
import httpx


@dataclass
class Attraction:
    id: str
    name: str
    description: str
    category: str
    rating: float
    price_level: int
    address: str
    lat: float
    lng: float
    opening_hours: list[str] = field(default_factory=list)
    estimated_cost: float = 0.0


async def get_attractions(
    city: str,
    interests: list[str],
    max_results: int = 10,
) -> list[Attraction]:
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        return _mock_attractions(city, interests)

    query = f"top attractions in {city} {' '.join(interests)}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params={"query": query, "key": api_key, "type": "tourist_attraction"},
            timeout=10.0,
        )
        if resp.status_code != 200:
            return _mock_attractions(city, interests)
        data = resp.json()

    attractions: list[Attraction] = []
    for place in data.get("results", [])[:max_results]:
        attractions.append(
            Attraction(
                id=place["place_id"],
                name=place["name"],
                description=place.get("formatted_address", ""),
                category="attraction",
                rating=place.get("rating", 0.0),
                price_level=place.get("price_level", 1),
                address=place.get("formatted_address", ""),
                lat=place["geometry"]["location"]["lat"],
                lng=place["geometry"]["location"]["lng"],
                estimated_cost=place.get("price_level", 1) * 15.0,
            )
        )
    return attractions or _mock_attractions(city, interests)


def _mock_attractions(city: str, interests: list[str]) -> list[Attraction]:
    base: list[Attraction] = [
        Attraction(
            id="MOCK-A1",
            name=f"{city} Historical Museum",
            description=f"The premier museum showcasing {city}'s rich history.",
            category="museum",
            rating=4.5,
            price_level=2,
            address=f"1 Museum Square, {city}",
            lat=0.0,
            lng=0.0,
            estimated_cost=20.0,
        ),
        Attraction(
            id="MOCK-A2",
            name=f"{city} Central Park",
            description=f"Beautiful urban park in the heart of {city}.",
            category="park",
            rating=4.7,
            price_level=0,
            address=f"Central Park, {city}",
            lat=0.0,
            lng=0.0,
            estimated_cost=0.0,
        ),
        Attraction(
            id="MOCK-A3",
            name=f"{city} Art Gallery",
            description=f"Contemporary and classical art collection.",
            category="art",
            rating=4.3,
            price_level=2,
            address=f"Gallery Row, {city}",
            lat=0.0,
            lng=0.0,
            estimated_cost=15.0,
        ),
        Attraction(
            id="MOCK-A4",
            name=f"{city} Food Market",
            description=f"Local street food and culinary delights.",
            category="food",
            rating=4.6,
            price_level=1,
            address=f"Market Street, {city}",
            lat=0.0,
            lng=0.0,
            estimated_cost=30.0,
        ),
    ]
    if "Adventure" in interests or "Outdoor" in interests:
        base.append(
            Attraction(
                id="MOCK-A5",
                name=f"{city} Adventure Park",
                description="Outdoor adventure activities.",
                category="adventure",
                rating=4.4,
                price_level=3,
                address=f"Adventure Zone, {city}",
                lat=0.0,
                lng=0.0,
                estimated_cost=60.0,
            )
        )
    return base
