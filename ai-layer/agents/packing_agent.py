"""PackingListAgent — generates a personalized packing list based on trip details."""
import os
import json
import openai
from .base import BaseAgent


SYSTEM_PROMPT = """You are a travel packing expert. Generate smart, comprehensive packing lists
tailored to the destination, duration, season, and activities planned. Group items by category.
Include items people commonly forget."""

PACKING_TOOL = {
    "type": "function",
    "function": {
        "name": "create_packing_list",
        "description": "Generate a personalized packing list for the trip",
        "parameters": {
            "type": "object",
            "properties": {
                "categories": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "items": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "item": {"type": "string"},
                                        "quantity": {"type": "string"},
                                        "essential": {"type": "boolean"},
                                        "note": {"type": "string"},
                                    },
                                    "required": ["item", "essential"],
                                },
                            },
                        },
                        "required": ["name", "items"],
                    },
                },
                "destination_specific_tips": {"type": "array", "items": {"type": "string"}},
                "total_items": {"type": "integer"},
            },
            "required": ["categories", "total_items"],
        },
    },
}


class PackingAgent(BaseAgent):
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def run(self, state: dict) -> dict:
        request = state.get("request", {})
        destination = request.get("destination", "")
        start_date = str(request.get("start_date", ""))
        end_date = str(request.get("end_date", ""))
        interests = request.get("interests", [])
        num_travelers = request.get("num_travelers", 1)

        itinerary = state.get("itinerary", {})
        weather = state.get("weather_forecast", [])

        weather_desc = ""
        if weather:
            temps = [w.get("temp_max", 25) for w in weather if isinstance(w, dict)]
            avg_temp = sum(temps) / len(temps) if temps else 25
            weather_desc = f"Average temperature: {avg_temp:.0f}°C"

        response = await self.client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Create a packing list for:\n"
                        f"Destination: {destination}\n"
                        f"Dates: {start_date} to {end_date}\n"
                        f"Travelers: {num_travelers}\n"
                        f"Interests/Activities: {', '.join(interests) or 'general tourism'}\n"
                        f"Weather: {weather_desc or 'Moderate, check forecast'}\n\n"
                        "Use the create_packing_list tool."
                    ),
                },
            ],
            tools=[PACKING_TOOL],
            tool_choice={"type": "function", "function": {"name": "create_packing_list"}},
        )

        tool_calls = response.choices[0].message.tool_calls
        if tool_calls:
            for tc in tool_calls:
                if tc.function.name == "create_packing_list":
                    return {"packing_list": json.loads(tc.function.arguments), **state}

        return {"packing_list": {"categories": [], "total_items": 0}, **state}
