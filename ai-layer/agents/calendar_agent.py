"""CalendarAgent — reads Google Calendar to find conflicts with trip dates."""
import os
from datetime import datetime, date, timedelta
from typing import Optional
import httpx
from .base import BaseAgent


class CalendarAgent(BaseAgent):
    async def run(self, state: dict) -> dict:
        request = state.get("request", {})
        user_token = state.get("google_calendar_token")

        start_date = datetime.strptime(str(request.get("start_date")), "%Y-%m-%d").date()
        end_date = datetime.strptime(str(request.get("end_date")), "%Y-%m-%d").date()

        if not user_token:
            return {**state, "calendar_conflicts": [], "calendar_checked": False}

        conflicts = await self._get_conflicts(user_token, start_date, end_date)
        return {**state, "calendar_conflicts": conflicts, "calendar_checked": True}

    async def _get_conflicts(
        self, token: dict, start: date, end: date
    ) -> list[dict]:
        access_token = token.get("access_token")
        if not access_token:
            return []

        time_min = datetime.combine(start, datetime.min.time()).isoformat() + "Z"
        time_max = datetime.combine(end + timedelta(days=1), datetime.min.time()).isoformat() + "Z"

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                    headers={"Authorization": f"Bearer {access_token}"},
                    params={
                        "timeMin": time_min,
                        "timeMax": time_max,
                        "singleEvents": True,
                        "orderBy": "startTime",
                    },
                    timeout=10.0,
                )
                if resp.status_code != 200:
                    return []
                data = resp.json()
        except Exception:
            return []

        conflicts = []
        for event in data.get("items", []):
            ev_start = event.get("start", {})
            conflicts.append({
                "event_id": event.get("id"),
                "summary": event.get("summary", "Busy"),
                "start": ev_start.get("dateTime", ev_start.get("date", "")),
                "end": event.get("end", {}).get("dateTime", event.get("end", {}).get("date", "")),
            })
        return conflicts


async def get_google_calendar_auth_url(redirect_uri: str) -> str:
    import urllib.parse
    params = {
        "client_id": os.getenv("GOOGLE_OAUTH_CLIENT_ID", ""),
        "redirect_uri": redirect_uri,
        "scope": "https://www.googleapis.com/auth/calendar.readonly",
        "response_type": "code",
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"


async def exchange_calendar_code(code: str, redirect_uri: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": os.getenv("GOOGLE_OAUTH_CLIENT_ID", ""),
                "client_secret": os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", ""),
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        resp.raise_for_status()
        return resp.json()
