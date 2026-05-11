"""BudgetAgent — validates total cost, reallocates budget across components."""
import os
import json
import openai
from .base import BaseAgent


SYSTEM_PROMPT = """You are a travel budget analyst. Given cost breakdowns from other agents,
compute the total, identify overspend, and suggest reallocation strategies. Be precise
with numbers. Categorize spending clearly."""

BUDGET_TOOL = {
    "type": "function",
    "function": {
        "name": "analyze_budget",
        "description": "Analyze and validate the trip budget",
        "parameters": {
            "type": "object",
            "properties": {
                "total_budget": {"type": "number"},
                "total_estimated_cost": {"type": "number"},
                "is_within_budget": {"type": "boolean"},
                "overspend_amount": {"type": "number"},
                "breakdown": {
                    "type": "object",
                    "properties": {
                        "flights": {"type": "number"},
                        "accommodation": {"type": "number"},
                        "experiences": {"type": "number"},
                        "food": {"type": "number"},
                        "transport": {"type": "number"},
                        "buffer": {"type": "number"},
                    },
                    "required": ["flights", "accommodation", "experiences", "food", "transport", "buffer"],
                },
                "reallocation_suggestions": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "savings_tips": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["total_budget", "total_estimated_cost", "is_within_budget", "overspend_amount", "breakdown", "reallocation_suggestions", "savings_tips"],
        },
    },
}


class BudgetAgent(BaseAgent):
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def run(self, state: dict) -> dict:
        request = state.get("request", {})
        total_budget = float(request.get("budget", 0))
        num_travelers = request.get("num_travelers", 1)

        flights = state.get("flights", {})
        hotels = state.get("hotels", {})
        itinerary = state.get("itinerary", {})

        flight_cost = flights.get("total_flight_cost", 0) * num_travelers
        hotel_cost = hotels.get("total_accommodation_cost", 0)
        experience_cost = itinerary.get("total_experience_cost", 0)

        response = await self.client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Analyze the budget for this trip:\n"
                        f"Total budget: ${total_budget} for {num_travelers} traveler(s)\n"
                        f"Flight costs: ${flight_cost:.2f}\n"
                        f"Accommodation costs: ${hotel_cost:.2f}\n"
                        f"Experience costs: ${experience_cost:.2f}\n"
                        f"Destination: {request.get('destination', '')}\n"
                        f"Number of days: {request.get('num_days', 5)}\n\n"
                        "Estimate food (~$50/person/day) and local transport (~$20/person/day). "
                        "Include a 10% buffer. Use the analyze_budget tool."
                    ),
                },
            ],
            tools=[BUDGET_TOOL],
            tool_choice={"type": "function", "function": {"name": "analyze_budget"}},
        )

        tool_calls = response.choices[0].message.tool_calls
        if tool_calls:
            for tc in tool_calls:
                if tc.function.name == "analyze_budget":
                    return {"budget_summary": json.loads(tc.function.arguments), **state}

        return {"budget_summary": {"total_budget": total_budget, "total_estimated_cost": 0, "is_within_budget": True, "overspend_amount": 0, "breakdown": {}, "reallocation_suggestions": [], "savings_tips": []}, **state}
