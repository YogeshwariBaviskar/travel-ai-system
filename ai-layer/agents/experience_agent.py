"""ExperienceAgent — builds day-wise attraction/food/event schedule."""
import os
import sys
import json
from datetime import datetime, timedelta
import openai

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from services.maps_service import get_attractions
from .base import BaseAgent


SYSTEM_PROMPT = """You are an expert local experience curator. Create immersive, practical
day-by-day itineraries using real attractions. Balance cultural experiences, food, relaxation,
and adventure based on traveler interests. Include timing, costs, and practical tips."""

EXPERIENCE_TOOL = {
    "type": "function",
    "function": {
        "name": "create_experience_plan",
        "description": "Create a detailed day-by-day experience schedule",
        "parameters": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "day_index": {"type": "integer"},
                            "date": {"type": "string"},
                            "theme": {"type": "string"},
                            "morning": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "description": {"type": "string"},
                                    "start_time": {"type": "string"},
                                    "duration_hours": {"type": "number"},
                                    "estimated_cost": {"type": "number"},
                                    "tips": {"type": "string"},
                                },
                                "required": ["name", "description", "start_time", "duration_hours", "estimated_cost"],
                            },
                            "afternoon": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "description": {"type": "string"},
                                    "start_time": {"type": "string"},
                                    "duration_hours": {"type": "number"},
                                    "estimated_cost": {"type": "number"},
                                    "tips": {"type": "string"},
                                },
                                "required": ["name", "description", "start_time", "duration_hours", "estimated_cost"],
                            },
                            "evening": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "description": {"type": "string"},
                                    "start_time": {"type": "string"},
                                    "duration_hours": {"type": "number"},
                                    "estimated_cost": {"type": "number"},
                                    "tips": {"type": "string"},
                                },
                                "required": ["name", "description", "start_time", "duration_hours", "estimated_cost"],
                            },
                            "transport_notes": {"type": "string"},
                            "daily_total_cost": {"type": "number"},
                        },
                        "required": ["day_index", "date", "theme", "morning", "afternoon", "evening", "daily_total_cost"],
                    },
                },
                "total_experience_cost": {"type": "number"},
                "cultural_tips": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["days", "total_experience_cost", "cultural_tips"],
        },
    },
}


class ExperienceAgent(BaseAgent):
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def run(self, state: dict) -> dict:
        request = state.get("request", {})
        destination = request.get("destination", "")
        start_date = datetime.strptime(str(request.get("start_date")), "%Y-%m-%d").date()
        end_date = datetime.strptime(str(request.get("end_date")), "%Y-%m-%d").date()
        num_days = max((end_date - start_date).days, 1)
        interests = request.get("interests", [])
        budget = request.get("budget", 5000)
        experience_budget = budget * 0.25  # ~25% for experiences

        attractions = await get_attractions(city=destination, interests=interests)
        attractions_text = "\n".join(
            f"- {a.name} ({a.category}): {a.description} | Rating:{a.rating} Cost:${a.estimated_cost}"
            for a in attractions
        )

        date_list = ", ".join(
            str(start_date + timedelta(days=i)) for i in range(num_days)
        )

        response = await self.client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Create a {num_days}-day experience plan for {destination}.\n"
                        f"Dates: {date_list}\n"
                        f"Interests: {', '.join(interests) or 'general sightseeing'}\n"
                        f"Experience budget: ${experience_budget:.0f} total\n"
                        f"Travelers: {request.get('num_travelers', 1)}\n\n"
                        f"Available attractions:\n{attractions_text}\n\n"
                        "Use create_experience_plan tool. Include cultural tips specific to this destination."
                    ),
                },
            ],
            tools=[EXPERIENCE_TOOL],
            tool_choice={"type": "function", "function": {"name": "create_experience_plan"}},
        )

        tool_calls = response.choices[0].message.tool_calls
        if tool_calls:
            for tc in tool_calls:
                if tc.function.name == "create_experience_plan":
                    return {"itinerary": json.loads(tc.function.arguments), **state}

        return {"itinerary": {"days": [], "total_experience_cost": 0, "cultural_tips": []}, **state}
