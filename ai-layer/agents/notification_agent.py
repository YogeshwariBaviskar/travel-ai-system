"""NotificationAgent — schedules reminders, weather alerts, check-in nudges."""
import os
import json
from datetime import datetime, timedelta
from typing import Optional
import httpx
from .base import BaseAgent


NOTIFICATION_TYPES = {
    "trip_reminder_7d": "Your trip starts in 7 days!",
    "trip_reminder_1d": "Your trip starts tomorrow!",
    "checkin_reminder": "Time to check in for your flight!",
    "weather_alert": "Weather alert for your destination",
    "itinerary_update": "Your itinerary has been updated",
    "replan_alert": "Your trip plan has been adjusted due to a disruption",
}


class NotificationAgent(BaseAgent):
    async def run(self, state: dict) -> dict:
        request = state.get("request", {})
        user_id = state.get("user_id", "")
        trip_id = state.get("trip_id", "")
        start_date_str = str(request.get("start_date", ""))

        if not start_date_str:
            return {**state, "notifications": []}

        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        scheduled: list[dict] = []

        scheduled.append({
            "type": "trip_reminder_7d",
            "scheduled_at": (start_date - timedelta(days=7)).isoformat(),
            "payload": {
                "title": "Trip Reminder",
                "body": f"Your trip to {request.get('destination', '')} starts in 7 days!",
                "trip_id": trip_id,
            },
        })

        scheduled.append({
            "type": "trip_reminder_1d",
            "scheduled_at": (start_date - timedelta(days=1)).isoformat(),
            "payload": {
                "title": "Trip Tomorrow!",
                "body": f"Your trip to {request.get('destination', '')} starts tomorrow. Have a great journey!",
                "trip_id": trip_id,
            },
        })

        flights = state.get("flights", {})
        if flights.get("recommendations"):
            flight = flights["recommendations"][0]
            dep_str = flight.get("departure", "")
            if dep_str:
                try:
                    dep_dt = datetime.fromisoformat(dep_str)
                    scheduled.append({
                        "type": "checkin_reminder",
                        "scheduled_at": (dep_dt - timedelta(hours=24)).isoformat(),
                        "payload": {
                            "title": "Flight Check-in Reminder",
                            "body": f"Check in for your {flight.get('airline', '')} flight now!",
                            "trip_id": trip_id,
                        },
                    })
                except ValueError:
                    pass

        return {**state, "notifications": scheduled}

    async def send_fcm(self, device_token: str, title: str, body: str, data: dict = None) -> bool:
        fcm_key = os.getenv("FCM_SERVER_KEY", "")
        if not fcm_key:
            return False

        payload = {
            "to": device_token,
            "notification": {"title": title, "body": body},
            "data": data or {},
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://fcm.googleapis.com/fcm/send",
                    headers={"Authorization": f"key={fcm_key}", "Content-Type": "application/json"},
                    json=payload,
                    timeout=10.0,
                )
                return resp.status_code == 200
        except Exception:
            return False

    async def send_sms(self, phone_number: str, message: str) -> bool:
        account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        from_number = os.getenv("TWILIO_FROM_NUMBER", "")
        if not all([account_sid, auth_token, from_number]):
            return False

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
                    auth=(account_sid, auth_token),
                    data={"From": from_number, "To": phone_number, "Body": message},
                    timeout=10.0,
                )
                return resp.status_code in (200, 201)
        except Exception:
            return False
