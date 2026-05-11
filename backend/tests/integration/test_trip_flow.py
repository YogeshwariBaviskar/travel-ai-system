"""Integration tests for the full trip-planning flow against a real test DB."""
import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.database import Base
from db.models import User, Trip
from api.main import app
from api.dependencies import get_current_user
from db.database import get_db

TEST_DB_URL = "sqlite:///./test_integration.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_user(db):
    user = User(
        id=str(uuid.uuid4()),
        email=f"test_{uuid.uuid4().hex[:6]}@example.com",
        name="Test User",
        google_id=str(uuid.uuid4()),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def client(db, test_user):
    def override_db():
        yield db

    def override_user():
        return test_user

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


MOCK_STATE = {
    "flights": {
        "recommendations": [
            {"flight_id": "F1", "rank": 1, "airline": "AA", "price": 350.0, "currency": "USD",
             "departure": "2026-07-01T08:00", "arrival": "2026-07-01T11:00",
             "duration": "PT3H", "stops": 0, "reason": "Best direct option"}
        ],
        "total_flight_cost": 350.0,
    },
    "hotels": {
        "recommendations": [
            {"hotel_id": "H1", "rank": 1, "name": "Grand Hotel", "area": "City Center",
             "price_per_night": 150.0, "total_hotel_cost": 750.0, "rating": 8.5,
             "amenities": ["WiFi", "Breakfast"], "reason": "Best value"}
        ],
        "recommended_hotel_id": "H1",
        "total_accommodation_cost": 750.0,
    },
    "itinerary": {
        "days": [
            {"day_index": 0, "date": "2026-07-01", "theme": "Arrival & Explore",
             "morning": {"name": "Museum", "description": "Art museum", "start_time": "09:00", "duration_hours": 3, "estimated_cost": 20},
             "afternoon": {"name": "Park", "description": "City park", "start_time": "13:00", "duration_hours": 2, "estimated_cost": 0},
             "evening": {"name": "Dinner", "description": "Local cuisine", "start_time": "19:00", "duration_hours": 2, "estimated_cost": 50},
             "daily_total_cost": 70}
        ],
        "total_experience_cost": 350.0,
        "cultural_tips": ["Book in advance", "Try local food"],
    },
    "budget_summary": {
        "total_budget": 3000.0,
        "total_estimated_cost": 1450.0,
        "is_within_budget": True,
        "overspend_amount": 0.0,
        "breakdown": {"flights": 350, "accommodation": 750, "experiences": 350, "food": 300, "transport": 150, "buffer": 100},
        "reallocation_suggestions": [],
        "savings_tips": ["Use public transport"],
    },
    "status": "complete",
    "errors": [],
}


def test_create_trip_multi_agent(client):
    response = client.post("/api/trips/", json={
        "destination": "Paris, France",
        "start_date": "2026-07-01",
        "end_date": "2026-07-06",
        "budget": 3000,
        "interests": ["Art", "Food"],
        "num_travelers": 1,
        "use_multi_agent": True,
    })

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "planning"
    assert "Paris" in data["title"]
    assert data["id"] is not None


def test_create_trip_single_agent(client):
    response = client.post("/api/trips/", json={
        "destination": "Rome, Italy",
        "start_date": "2026-07-01",
        "end_date": "2026-07-06",
        "budget": 2000,
        "use_multi_agent": False,
    })

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "planning"
    assert "Rome" in data["title"]
    assert data["id"] is not None


def test_list_trips(client, db, test_user):
    trip = Trip(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        title="Test Trip",
        status="complete",
    )
    db.add(trip)
    db.commit()

    response = client.get("/api/trips/")
    assert response.status_code == 200
    trips = response.json()
    assert any(t["title"] == "Test Trip" for t in trips)


def test_get_trip(client, db, test_user):
    trip = Trip(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        title="Specific Trip",
        status="complete",
        plan={"flights": {}, "hotels": {}},
        agent_state=MOCK_STATE,
    )
    db.add(trip)
    db.commit()

    response = client.get(f"/api/trips/{trip.id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Specific Trip"


def test_get_trip_not_found(client):
    response = client.get(f"/api/trips/{uuid.uuid4()}")
    assert response.status_code == 404


def test_explain_trip(client, db, test_user):
    trip = Trip(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        title="Explained Trip",
        status="complete",
        plan=MOCK_STATE,
        agent_state=MOCK_STATE,
    )
    db.add(trip)
    db.commit()

    response = client.post(f"/api/trips/{trip.id}/explain")
    assert response.status_code == 200
    data = response.json()
    assert "flight_selection" in data
    assert "budget_analysis" in data


def test_delete_trip(client, db, test_user):
    trip = Trip(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        title="Delete Me",
        status="complete",
    )
    db.add(trip)
    db.commit()

    response = client.delete(f"/api/trips/{trip.id}")
    assert response.status_code == 204

    response = client.get(f"/api/trips/{trip.id}")
    assert response.status_code == 404
