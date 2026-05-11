"""FlightAgent — queries Amadeus, ranks by price/time, uses OpenAI to summarize."""
import os
import sys
import json
from datetime import datetime
import openai

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from services.flight_service import search_flights, FlightOption
from .base import BaseAgent


SYSTEM_PROMPT = """You are a flight search specialist. Given flight options, analyze them and
select the best 3 ranked by value (price/duration ratio). Return structured recommendations
with clear reasoning for each choice. Always respect the budget ceiling."""

FLIGHT_TOOL = {
    "type": "function",
    "function": {
        "name": "select_flights",
        "description": "Select and rank the top flight options",
        "parameters": {
            "type": "object",
            "properties": {
                "recommendations": {
                    "type": "array",
                    "maxItems": 3,
                    "items": {
                        "type": "object",
                        "properties": {
                            "flight_id": {"type": "string"},
                            "rank": {"type": "integer"},
                            "airline": {"type": "string"},
                            "price": {"type": "number"},
                            "currency": {"type": "string"},
                            "departure": {"type": "string"},
                            "arrival": {"type": "string"},
                            "duration": {"type": "string"},
                            "stops": {"type": "integer"},
                            "reason": {"type": "string", "description": "Why this option is recommended"},
                        },
                        "required": ["flight_id", "rank", "airline", "price", "currency", "departure", "arrival", "duration", "stops", "reason"],
                    },
                },
                "total_flight_cost": {"type": "number"},
                "notes": {"type": "string"},
            },
            "required": ["recommendations", "total_flight_cost"],
        },
    },
}


class FlightAgent(BaseAgent):
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def run(self, state: dict) -> dict:
        request = state.get("request", {})
        origin = request.get("origin_airport", "JFK")
        destination = request.get("destination_airport", request.get("destination", ""))
        start_date_str = request.get("start_date")
        budget = request.get("budget", 5000)
        num_travelers = request.get("num_travelers", 1)

        start_date = datetime.strptime(str(start_date_str), "%Y-%m-%d").date()
        flight_budget = budget * 0.35  # ~35% of total budget for flights

        flights = await search_flights(
            origin=origin,
            destination=destination[:3].upper() if len(destination) >= 3 else destination,
            departure_date=start_date,
            adults=num_travelers,
            max_price=flight_budget,
        )

        flights_text = "\n".join(
            f"- ID:{f.id} {f.airline} ${f.price} | Dep:{f.departure} Arr:{f.arrival} "
            f"Duration:{f.duration} Stops:{f.stops}"
            for f in flights
        )

        response = await self.client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Select the best flight options from {origin} to {destination}.\n"
                        f"Budget ceiling: ${flight_budget:.0f} for {num_travelers} traveler(s)\n"
                        f"Available flights:\n{flights_text}\n\n"
                        "Use the select_flights tool to return ranked recommendations."
                    ),
                },
            ],
            tools=[FLIGHT_TOOL],
            tool_choice={"type": "function", "function": {"name": "select_flights"}},
        )

        tool_calls = response.choices[0].message.tool_calls
        if tool_calls:
            for tc in tool_calls:
                if tc.function.name == "select_flights":
                    result = json.loads(tc.function.arguments)
                    result["raw_options"] = [f.__dict__ for f in flights]
                    return {"flights": result, **state}

        return {"flights": {"recommendations": [], "total_flight_cost": 0}, **state}
