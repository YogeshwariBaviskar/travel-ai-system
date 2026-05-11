import asyncio
import json
import os
import sys
import uuid
from datetime import date
from typing import List, Optional, AsyncGenerator

import openai

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from api.dependencies import get_current_user, get_user_by_token
from db.database import get_db, SessionLocal
from db.models import Trip, TripFlight, TripHotel, ItineraryDay, User

_ai_layer_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ai-layer"))
if _ai_layer_path not in sys.path:
    sys.path.insert(0, _ai_layer_path)

try:
    from orchestrator import run_planning
except ImportError:  # ai-layer not available in some test environments
    run_planning = None

router = APIRouter()


class CreateTripRequest(BaseModel):
    destination: str
    start_date: date
    end_date: date
    budget: float
    interests: List[str] = []
    num_travelers: int = 1
    origin_airport: str = "JFK"
    use_multi_agent: bool = True


class TripResponse(BaseModel):
    id: str
    title: str
    status: str
    raw_request: Optional[dict]
    plan: Optional[dict]
    agent_state: Optional[dict]
    created_at: str

    model_config = {"from_attributes": True}


def _serialize(trip: Trip) -> dict:
    return {
        "id": trip.id,
        "title": trip.title,
        "status": trip.status,
        "raw_request": trip.raw_request,
        "plan": trip.plan,
        "agent_state": trip.agent_state,
        "created_at": trip.created_at.isoformat() if trip.created_at else None,
    }


def _persist_agent_state(trip: Trip, state: dict, db: Session) -> None:
    """Persist detailed agent results to normalized tables."""
    flights = state.get("flights", {})
    hotels = state.get("hotels", {})
    itinerary = state.get("itinerary", {})

    for rec in (flights.get("recommendations") or [])[:1]:
        db.add(TripFlight(
            id=str(uuid.uuid4()),
            trip_id=trip.id,
            provider_ref=rec.get("flight_id"),
            details=rec,
            price=rec.get("price"),
            currency=rec.get("currency", "USD"),
        ))

    recommended_hotel_id = hotels.get("recommended_hotel_id")
    for rec in (hotels.get("recommendations") or [])[:1]:
        if not recommended_hotel_id or rec.get("hotel_id") == recommended_hotel_id:
            db.add(TripHotel(
                id=str(uuid.uuid4()),
                trip_id=trip.id,
                provider_ref=rec.get("hotel_id"),
                details=rec,
                price=rec.get("price_per_night"),
                currency="USD",
            ))

    for day in (itinerary.get("days") or []):
        db.add(ItineraryDay(
            id=str(uuid.uuid4()),
            trip_id=trip.id,
            day_index=day.get("day_index", 0),
            date=day.get("date"),
            activities=day,
        ))


@router.post("/", response_model=dict)
def create_trip(
    request: CreateTripRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    trip = Trip(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        title=f"Trip to {request.destination}",
        status="planning",
        raw_request=request.model_dump(mode="json"),
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)

    return _serialize(trip)


def _delete_trip_by_id(trip_id: str) -> None:
    with SessionLocal() as s:
        t = s.query(Trip).filter(Trip.id == trip_id).first()
        if t:
            s.delete(t)
            s.commit()


def _save_trip_result(trip_id: str, state: dict) -> dict:
    with SessionLocal() as write_db:
        saved_trip = write_db.query(Trip).filter(Trip.id == trip_id).first()
        if not saved_trip:
            return {}
        saved_trip.agent_state = dict(state)
        saved_trip.plan = {
            "flights": state.get("flights"),
            "hotels": state.get("hotels"),
            "itinerary": state.get("itinerary"),
            "budget_summary": state.get("budget_summary"),
        }
        saved_trip.status = state.get("status", "complete")
        _persist_agent_state(saved_trip, dict(state), write_db)
        write_db.commit()
        return saved_trip.plan or {}


@router.get("/stream/{trip_id}")
async def stream_trip_planning(
    trip_id: str,
    request: Request,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    """SSE endpoint that streams planning progress events for a trip.
    Accepts the JWT as a query param because EventSource cannot send custom headers.
    """
    current_user = get_user_by_token(token, db)
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Extract data and release the DB connection before the long planning phase so
    # the connection pool isn't exhausted while run_planning holds this request open.
    trip_id_str = trip.id
    user_id_str = current_user.id
    req_dict = trip.raw_request or {}
    db.close()

    async def event_generator() -> AsyncGenerator[dict, None]:
        yield {"event": "status", "data": json.dumps({"status": "starting", "message": "Initializing multi-agent planning..."})}
        await asyncio.sleep(0.1)

        stages = [
            ("context", "Loading user preference context..."),
            ("flights", "FlightAgent searching Amadeus for best fares..."),
            ("hotels", "HotelAgent scanning Booking.com for accommodations..."),
            ("experience", "ExperienceAgent building day-by-day itinerary..."),
            ("budget", "BudgetAgent validating costs and rebalancing budget..."),
            ("finalizing", "Finalizing your personalized trip plan..."),
        ]

        for stage, message in stages:
            if await request.is_disconnected():
                return
            yield {"event": "progress", "data": json.dumps({"stage": stage, "message": message})}
            await asyncio.sleep(0.5)

        try:
            if run_planning is None:
                raise ImportError("orchestrator not available")
            state = await run_planning(user_id=user_id_str, request=req_dict)

            if state.get("status") == "failed":
                await asyncio.to_thread(_delete_trip_by_id, trip_id_str)
                agent_errors = state.get("errors") or []
                failed_agents = [e["agent"] for e in agent_errors if "agent" in e]
                if failed_agents:
                    message = f"Planning failed in {', '.join(failed_agents)}. Please try again or adjust your request."
                else:
                    message = "The AI could not generate a complete itinerary. Try adjusting your destination, dates, or budget."
                yield {"event": "error", "data": json.dumps({"error": message, "code": "planning_failed"})}
            else:
                plan = await asyncio.to_thread(_save_trip_result, trip_id_str, state)
                yield {"event": "complete", "data": json.dumps({"status": "complete", "plan": plan})}
        except ImportError:
            await asyncio.to_thread(_delete_trip_by_id, trip_id_str)
            yield {"event": "error", "data": json.dumps({
                "error": "The planning service is unavailable. Please try again later.",
                "code": "service_unavailable",
            })}
        except openai.RateLimitError as exc:
            await asyncio.to_thread(_delete_trip_by_id, trip_id_str)
            if "insufficient_quota" in str(exc) or "exceeded your current quota" in str(exc):
                message = "OpenAI API credits exhausted. Please top up your account at platform.openai.com/account/billing."
                code = "quota_exceeded"
            else:
                message = "OpenAI rate limit reached. Please wait a moment and try again."
                code = "rate_limit"
            yield {"event": "error", "data": json.dumps({"error": message, "code": code})}
        except openai.AuthenticationError:
            await asyncio.to_thread(_delete_trip_by_id, trip_id_str)
            yield {"event": "error", "data": json.dumps({
                "error": "Invalid OpenAI API key. Please check your server configuration.",
                "code": "auth_error",
            })}
        except openai.APITimeoutError:
            await asyncio.to_thread(_delete_trip_by_id, trip_id_str)
            yield {"event": "error", "data": json.dumps({
                "error": "The AI service timed out. Please try again in a moment.",
                "code": "timeout",
            })}
        except openai.APIConnectionError:
            await asyncio.to_thread(_delete_trip_by_id, trip_id_str)
            yield {"event": "error", "data": json.dumps({
                "error": "Could not connect to the AI service. Check your connection and try again.",
                "code": "connection_error",
            })}
        except Exception:
            await asyncio.to_thread(_delete_trip_by_id, trip_id_str)
            yield {"event": "error", "data": json.dumps({
                "error": "An unexpected error occurred while planning your trip. Please try again.",
                "code": "unknown_error",
            })}

    return EventSourceResponse(event_generator())


@router.get("/", response_model=List[dict])
def list_trips(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    trips = (
        db.query(Trip)
        .filter(Trip.user_id == current_user.id)
        .order_by(Trip.created_at.desc())
        .all()
    )
    return [_serialize(t) for t in trips]


@router.get("/{trip_id}", response_model=dict)
def get_trip(
    trip_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return _serialize(trip)


@router.delete("/{trip_id}", status_code=204)
def delete_trip(
    trip_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    db.delete(trip)
    db.commit()


@router.post("/{trip_id}/explain")
def explain_trip(
    trip_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return agent decision transparency for a completed trip."""
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    if trip.status != "complete":
        raise HTTPException(status_code=400, detail="Trip planning not complete")

    state = trip.agent_state or {}
    flights = state.get("flights", {})
    hotels = state.get("hotels", {})
    budget = state.get("budget_summary", {})

    explanation = {
        "flight_selection": {
            "chosen": (flights.get("recommendations") or [{}])[0],
            "reason": (flights.get("recommendations") or [{}])[0].get("reason", "Best value for money"),
            "alternatives_considered": len(flights.get("recommendations", [])),
        },
        "hotel_selection": {
            "chosen": (hotels.get("recommendations") or [{}])[0],
            "reason": (hotels.get("recommendations") or [{}])[0].get("reason", "Best amenities/price ratio"),
            "alternatives_considered": len(hotels.get("recommendations", [])),
        },
        "budget_analysis": budget,
        "agent_errors": state.get("errors", []),
        "user_context_applied": bool(state.get("user_context")),
    }
    return explanation
