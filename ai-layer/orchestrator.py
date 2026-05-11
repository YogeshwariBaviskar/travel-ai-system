"""LangGraph orchestration graph for multi-agent trip planning."""
from __future__ import annotations

import asyncio
from typing import TypedDict, Literal, Any

from langgraph.graph import StateGraph, END

from agents.flight_agent import FlightAgent
from agents.hotel_agent import HotelAgent
from agents.experience_agent import ExperienceAgent
from agents.budget_agent import BudgetAgent
from memory.vector_store import get_vector_store


class TripState(TypedDict, total=False):
    user_id: str
    request: dict
    flights: dict
    hotels: dict
    itinerary: dict
    budget_summary: dict
    calendar_conflicts: list
    notifications: list
    errors: list
    status: Literal["planning", "complete", "replanning", "failed"]
    user_context: str


async def _load_user_context(state: TripState) -> TripState:
    """Inject user preference context from vector store."""
    user_id = state.get("user_id", "")
    request = state.get("request", {})
    if user_id:
        store = get_vector_store()
        context = await store.get_user_context(
            user_id=user_id,
            query=f"{request.get('destination', '')} {' '.join(request.get('interests', []))}",
        )
        return {**state, "user_context": context, "status": "planning"}
    return {**state, "status": "planning"}


async def _run_flight_agent(state: TripState) -> TripState:
    try:
        agent = FlightAgent()
        result = await agent.run(dict(state))
        return {**state, **result}
    except Exception as exc:
        errors = list(state.get("errors") or [])
        errors.append({"agent": "FlightAgent", "error": str(exc)})
        return {**state, "errors": errors, "flights": {"recommendations": [], "total_flight_cost": 0}}


async def _run_hotel_agent(state: TripState) -> TripState:
    try:
        agent = HotelAgent()
        result = await agent.run(dict(state))
        return {**state, **result}
    except Exception as exc:
        errors = list(state.get("errors") or [])
        errors.append({"agent": "HotelAgent", "error": str(exc)})
        return {**state, "errors": errors, "hotels": {"recommendations": [], "total_accommodation_cost": 0}}


async def _run_experience_agent(state: TripState) -> TripState:
    try:
        agent = ExperienceAgent()
        result = await agent.run(dict(state))
        return {**state, **result}
    except Exception as exc:
        errors = list(state.get("errors") or [])
        errors.append({"agent": "ExperienceAgent", "error": str(exc)})
        return {**state, "errors": errors, "itinerary": {"days": [], "total_experience_cost": 0, "cultural_tips": []}}


async def _run_parallel_agents(state: TripState) -> TripState:
    """Run flight, hotel, and experience agents in parallel."""
    flight_agent = FlightAgent()
    hotel_agent = HotelAgent()
    experience_agent = ExperienceAgent()

    errors = list(state.get("errors") or [])
    results = await asyncio.gather(
        flight_agent.run(dict(state)),
        hotel_agent.run(dict(state)),
        experience_agent.run(dict(state)),
        return_exceptions=True,
    )

    new_state = dict(state)
    for result, name in zip(results, ["FlightAgent", "HotelAgent", "ExperienceAgent"]):
        if isinstance(result, Exception):
            errors.append({"agent": name, "error": str(result)})
        else:
            new_state.update(result)

    new_state["errors"] = errors
    return new_state  # type: ignore[return-value]


async def _run_budget_agent(state: TripState) -> TripState:
    try:
        agent = BudgetAgent()
        result = await agent.run(dict(state))
        return {**state, **result}
    except Exception as exc:
        errors = list(state.get("errors") or [])
        errors.append({"agent": "BudgetAgent", "error": str(exc)})
        return {**state, "errors": errors}


async def _finalize(state: TripState) -> TripState:
    """Persist preference context and set final status."""
    user_id = state.get("user_id", "")
    request = state.get("request", {})
    budget_summary = state.get("budget_summary", {})

    if user_id and budget_summary.get("is_within_budget"):
        store = get_vector_store()
        interests = request.get("interests", [])
        dest = request.get("destination", "")
        if interests and dest:
            await store.store_preference(
                user_id=user_id,
                preference=f"Enjoyed a trip to {dest} with interests: {', '.join(interests)}",
                metadata={"destination": dest, "budget": request.get("budget")},
            )

    errors = state.get("errors") or []
    status = "failed" if (errors and not state.get("itinerary")) else "complete"
    return {**state, "status": status}


def build_graph() -> Any:
    """Build and compile the LangGraph planning graph."""
    builder = StateGraph(TripState)

    builder.add_node("load_context", _load_user_context)
    builder.add_node("parallel_agents", _run_parallel_agents)
    builder.add_node("budget", _run_budget_agent)
    builder.add_node("finalize", _finalize)

    builder.set_entry_point("load_context")
    builder.add_edge("load_context", "parallel_agents")
    builder.add_edge("parallel_agents", "budget")
    builder.add_edge("budget", "finalize")
    builder.add_edge("finalize", END)

    return builder.compile()


async def run_planning(user_id: str, request: dict) -> TripState:
    """Entry point: run the full multi-agent planning graph."""
    graph = build_graph()
    initial_state: TripState = {
        "user_id": user_id,
        "request": request,
        "errors": [],
        "calendar_conflicts": [],
        "notifications": [],
    }
    result = await graph.ainvoke(initial_state)
    return result
