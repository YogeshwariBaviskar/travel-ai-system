"""HotelAgent — queries Booking.com, filters by budget and proximity."""
import os
import sys
import json
from datetime import datetime
import openai

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from services.hotel_service import search_hotels
from .base import BaseAgent


SYSTEM_PROMPT = """You are a hotel selection specialist. Analyze hotel options and recommend
the best 3 based on value, amenities, location, and ratings. Always stay within the nightly
budget. Explain why each hotel suits the traveler's needs."""

HOTEL_TOOL = {
    "type": "function",
    "function": {
        "name": "select_hotels",
        "description": "Select and rank the best hotel options",
        "parameters": {
            "type": "object",
            "properties": {
                "recommendations": {
                    "type": "array",
                    "maxItems": 3,
                    "items": {
                        "type": "object",
                        "properties": {
                            "hotel_id": {"type": "string"},
                            "rank": {"type": "integer"},
                            "name": {"type": "string"},
                            "area": {"type": "string"},
                            "price_per_night": {"type": "number"},
                            "total_hotel_cost": {"type": "number"},
                            "rating": {"type": "number"},
                            "amenities": {"type": "array", "items": {"type": "string"}},
                            "reason": {"type": "string"},
                        },
                        "required": ["hotel_id", "rank", "name", "area", "price_per_night", "total_hotel_cost", "rating", "amenities", "reason"],
                    },
                },
                "recommended_hotel_id": {"type": "string"},
                "total_accommodation_cost": {"type": "number"},
            },
            "required": ["recommendations", "recommended_hotel_id", "total_accommodation_cost"],
        },
    },
}


class HotelAgent(BaseAgent):
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def run(self, state: dict) -> dict:
        request = state.get("request", {})
        city = request.get("destination", "")
        start_date = datetime.strptime(str(request.get("start_date")), "%Y-%m-%d").date()
        end_date = datetime.strptime(str(request.get("end_date")), "%Y-%m-%d").date()
        num_days = max((end_date - start_date).days, 1)
        budget = request.get("budget", 5000)
        num_travelers = request.get("num_travelers", 1)
        hotel_budget_per_night = (budget * 0.4) / num_days

        hotels = await search_hotels(
            city=city,
            check_in=start_date,
            check_out=end_date,
            adults=num_travelers,
            max_price_per_night=hotel_budget_per_night * 1.2,
        )

        hotels_text = "\n".join(
            f"- ID:{h.id} {h.name} ({h.area}) ${h.price_per_night}/night "
            f"Rating:{h.rating} Amenities:{','.join(h.amenities)}"
            for h in hotels
        )

        response = await self.client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Select the best hotels in {city} for {num_days} nights.\n"
                        f"Budget: ${hotel_budget_per_night:.0f}/night, {num_travelers} traveler(s)\n"
                        f"Trip preferences: {request.get('interests', [])}\n"
                        f"Available hotels:\n{hotels_text}\n\n"
                        "Use the select_hotels tool to return ranked recommendations."
                    ),
                },
            ],
            tools=[HOTEL_TOOL],
            tool_choice={"type": "function", "function": {"name": "select_hotels"}},
        )

        tool_calls = response.choices[0].message.tool_calls
        if tool_calls:
            for tc in tool_calls:
                if tc.function.name == "select_hotels":
                    result = json.loads(tc.function.arguments)
                    result["raw_options"] = [h.__dict__ for h in hotels]
                    return {"hotels": result, **state}

        return {"hotels": {"recommendations": [], "total_accommodation_cost": 0}, **state}
