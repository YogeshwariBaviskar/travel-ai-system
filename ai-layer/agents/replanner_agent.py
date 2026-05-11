"""ReplannerAgent — triggered by disruptions (delay, cancellation, weather)."""
import os
import json
import openai
from .base import BaseAgent


SYSTEM_PROMPT = """You are an expert travel replanner. When disruptions occur (flight delays,
cancellations, severe weather), you update the minimum necessary parts of the itinerary
while preserving as much of the original plan as possible. Explain every change clearly."""

REPLAN_TOOL = {
    "type": "function",
    "function": {
        "name": "replan_trip",
        "description": "Generate an updated trip plan after a disruption",
        "parameters": {
            "type": "object",
            "properties": {
                "disruption_type": {"type": "string", "enum": ["flight_delay", "flight_cancellation", "weather", "hotel_issue", "manual"]},
                "summary": {"type": "string", "description": "One-sentence summary of what changed"},
                "changes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "component": {"type": "string"},
                            "original": {"type": "string"},
                            "updated": {"type": "string"},
                            "reason": {"type": "string"},
                        },
                        "required": ["component", "original", "updated", "reason"],
                    },
                },
                "updated_flights": {"type": "object"},
                "updated_itinerary_days": {"type": "array"},
                "cost_impact": {"type": "number", "description": "Additional cost (negative = savings)"},
                "user_action_required": {"type": "boolean"},
                "user_action_description": {"type": "string"},
            },
            "required": ["disruption_type", "summary", "changes", "cost_impact", "user_action_required"],
        },
    },
}


class ReplannerAgent(BaseAgent):
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def run(self, state: dict) -> dict:
        return await self.replan(state)

    async def replan(self, state: dict, disruption: dict = None) -> dict:
        if disruption is None:
            disruption = state.get("disruption", {})

        current_plan = state.get("plan", {})
        request = state.get("request", {})

        disruption_desc = (
            f"Type: {disruption.get('type', 'unknown')}\n"
            f"Details: {disruption.get('details', 'No details provided')}\n"
            f"Affected: {disruption.get('affected_component', 'Unknown component')}\n"
            f"Severity: {disruption.get('severity', 'moderate')}"
        )

        response = await self.client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"A disruption has occurred for a trip to {request.get('destination', '')}.\n\n"
                        f"DISRUPTION:\n{disruption_desc}\n\n"
                        f"CURRENT PLAN SUMMARY:\n"
                        f"- Flights: {current_plan.get('flights', {}).get('recommendations', [{}])[0] if current_plan.get('flights', {}).get('recommendations') else 'No flights'}\n"
                        f"- Hotel: {current_plan.get('hotels', {}).get('recommendations', [{}])[0] if current_plan.get('hotels', {}).get('recommendations') else 'No hotels'}\n"
                        f"- Days: {len(current_plan.get('itinerary', {}).get('days', []))}\n\n"
                        "Replan with minimal changes. Use the replan_trip tool."
                    ),
                },
            ],
            tools=[REPLAN_TOOL],
            tool_choice={"type": "function", "function": {"name": "replan_trip"}},
        )

        tool_calls = response.choices[0].message.tool_calls
        if tool_calls:
            for tc in tool_calls:
                if tc.function.name == "replan_trip":
                    return {
                        **state,
                        "replan": json.loads(tc.function.arguments),
                        "status": "replanning",
                    }

        return {**state, "replan": {"summary": "No changes needed", "changes": []}, "status": "complete"}
