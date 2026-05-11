import os
import json
from datetime import datetime
import openai
from agents.base import BaseAgent

SYSTEM_PROMPT = """You are an expert travel planner with deep knowledge of destinations worldwide.
Create detailed, practical, and enjoyable travel itineraries.
Always respect budget constraints and traveler preferences.
Provide specific, real recommendations for attractions, restaurants, and accommodations."""

TRIP_PLAN_TOOL = {
    "type": "function",
    "function": {
        "name": "create_trip_plan",
        "description": "Create a structured day-by-day travel itinerary",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Catchy trip title"},
                "summary": {"type": "string", "description": "2-3 sentence overview of the trip"},
                "total_days": {"type": "integer"},
                "estimated_total_cost": {"type": "number", "description": "Total cost in specified currency"},
                "currency": {"type": "string", "default": "USD"},
                "days": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "day": {"type": "integer"},
                            "date": {"type": "string"},
                            "location": {"type": "string"},
                            "morning": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "description": {"type": "string"},
                                    "duration_hours": {"type": "number"},
                                    "estimated_cost": {"type": "number"},
                                },
                                "required": ["name", "description", "duration_hours", "estimated_cost"],
                            },
                            "afternoon": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "description": {"type": "string"},
                                    "duration_hours": {"type": "number"},
                                    "estimated_cost": {"type": "number"},
                                },
                                "required": ["name", "description", "duration_hours", "estimated_cost"],
                            },
                            "evening": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "description": {"type": "string"},
                                    "duration_hours": {"type": "number"},
                                    "estimated_cost": {"type": "number"},
                                },
                                "required": ["name", "description", "duration_hours", "estimated_cost"],
                            },
                            "accommodation": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "area": {"type": "string"},
                                    "cost_per_night": {"type": "number"},
                                },
                                "required": ["name", "area", "cost_per_night"],
                            },
                        },
                        "required": ["day", "date", "location", "morning", "afternoon", "evening", "accommodation"],
                    },
                },
                "tips": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Practical travel tips for this destination",
                },
            },
            "required": ["title", "summary", "total_days", "estimated_total_cost", "currency", "days", "tips"],
        },
    },
}


class PlannerAgent(BaseAgent):
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def run(self, input: dict) -> dict:
        return await self.plan(input)

    async def plan(self, request: dict) -> dict:
        start = datetime.strptime(str(request["start_date"]), "%Y-%m-%d")
        end = datetime.strptime(str(request["end_date"]), "%Y-%m-%d")
        num_days = max((end - start).days, 1)
        interests_str = ", ".join(request.get("interests", [])) or "general sightseeing"

        user_message = (
            f"Plan a {num_days}-day trip to {request['destination']}.\n"
            f"Budget: ${request['budget']} total for {request.get('num_travelers', 1)} traveler(s)\n"
            f"Dates: {request['start_date']} to {request['end_date']}\n"
            f"Interests: {interests_str}\n\n"
            "Use the create_trip_plan tool to return a complete itinerary."
        )

        response = await self.client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            tools=[TRIP_PLAN_TOOL],
            tool_choice={"type": "function", "function": {"name": "create_trip_plan"}},
        )

        tool_calls = response.choices[0].message.tool_calls
        if tool_calls:
            for tc in tool_calls:
                if tc.function.name == "create_trip_plan":
                    return json.loads(tc.function.arguments)

        raise ValueError("PlannerAgent: no trip plan returned by the model")
