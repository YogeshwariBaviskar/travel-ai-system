"""Webhook receivers for flight status and weather alerts."""
import json
import os
import asyncio
import redis
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Header, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.database import SessionLocal
from db.models import Trip, Notification

router = APIRouter()

_redis: Optional[redis.Redis] = None


def _get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
    return _redis


class FlightStatusWebhook(BaseModel):
    flight_id: str
    trip_id: str
    event_type: str  # "DELAY" | "CANCELLATION" | "GATE_CHANGE" | "ON_TIME"
    delay_minutes: Optional[int] = None
    new_departure: Optional[str] = None
    details: Optional[str] = None


class WeatherAlertWebhook(BaseModel):
    city: str
    alert_type: str
    severity: str
    description: str
    affected_date: str
    affected_trip_ids: Optional[list[str]] = None


async def _trigger_replan(trip_id: str, disruption: dict) -> None:
    """Background task: replan a trip and publish update to WebSocket channel."""
    db = SessionLocal()
    try:
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip or trip.status not in ("complete", "replanning"):
            return

        trip.status = "replanning"
        db.commit()

        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "ai-layer"))
        from ai_layer.agents.replanner_agent import ReplannerAgent

        agent = ReplannerAgent()
        state = {
            "plan": trip.plan or {},
            "request": trip.raw_request or {},
            "trip_id": trip_id,
            "user_id": trip.user_id,
            "disruption": disruption,
        }
        result = await agent.replan(state, disruption=disruption)

        trip.agent_state = {**(trip.agent_state or {}), "replan": result.get("replan")}
        trip.status = "complete"
        db.commit()

        notification = Notification(
            trip_id=trip_id,
            user_id=trip.user_id,
            type="replan_alert",
            payload={"disruption": disruption, "changes": result.get("replan", {}).get("changes", [])},
        )
        db.add(notification)
        db.commit()

        r = _get_redis()
        r.publish(
            f"trip:{trip_id}:updates",
            json.dumps({"event": "replan", "trip_id": trip_id, "replan": result.get("replan")}),
        )
    except Exception as exc:
        db.query(Trip).filter(Trip.id == trip_id).update({"status": "failed"})
        db.commit()
        raise
    finally:
        db.close()


@router.post("/flight-status")
async def flight_status_webhook(
    payload: FlightStatusWebhook,
    background_tasks: BackgroundTasks,
    x_webhook_secret: str = Header(default=""),
):
    expected_secret = os.getenv("WEBHOOK_SECRET", "")
    if expected_secret and x_webhook_secret != expected_secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    if payload.event_type in ("DELAY", "CANCELLATION"):
        disruption = {
            "type": "flight_delay" if payload.event_type == "DELAY" else "flight_cancellation",
            "affected_component": f"Flight {payload.flight_id}",
            "details": (
                f"{payload.event_type}: {payload.delay_minutes or 0} minutes delay. "
                f"New departure: {payload.new_departure or 'TBD'}. {payload.details or ''}"
            ),
            "severity": "high" if payload.event_type == "CANCELLATION" else "moderate",
            "timestamp": datetime.utcnow().isoformat(),
        }
        background_tasks.add_task(_trigger_replan, payload.trip_id, disruption)
        return {"status": "accepted", "message": f"Replanning triggered for trip {payload.trip_id}"}

    return {"status": "ignored", "event_type": payload.event_type}


@router.post("/weather-alert")
async def weather_alert_webhook(
    payload: WeatherAlertWebhook,
    background_tasks: BackgroundTasks,
    x_webhook_secret: str = Header(default=""),
):
    expected_secret = os.getenv("WEBHOOK_SECRET", "")
    if expected_secret and x_webhook_secret != expected_secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    disruption = {
        "type": "weather",
        "affected_component": f"Day on {payload.affected_date} in {payload.city}",
        "details": f"{payload.alert_type}: {payload.description}",
        "severity": payload.severity,
        "timestamp": datetime.utcnow().isoformat(),
    }

    trip_ids = payload.affected_trip_ids or []
    if not trip_ids:
        db = SessionLocal()
        try:
            trips = db.query(Trip).filter(Trip.status == "complete").all()
            trip_ids = [
                t.id for t in trips
                if t.raw_request and t.raw_request.get("destination", "").lower() in payload.city.lower()
            ]
        finally:
            db.close()

    for trip_id in trip_ids:
        background_tasks.add_task(_trigger_replan, trip_id, disruption)

    return {"status": "accepted", "trips_affected": len(trip_ids)}


@router.post("/simulate-disruption/{trip_id}")
async def simulate_disruption(
    trip_id: str,
    background_tasks: BackgroundTasks,
    disruption_type: str = "flight_delay",
):
    """Dev endpoint to test disruption flow."""
    disruption = {
        "type": disruption_type,
        "affected_component": "Outbound flight",
        "details": "Simulated disruption: 3-hour delay due to maintenance.",
        "severity": "moderate",
        "timestamp": datetime.utcnow().isoformat(),
    }
    background_tasks.add_task(_trigger_replan, trip_id, disruption)
    return {"status": "simulated", "trip_id": trip_id}
