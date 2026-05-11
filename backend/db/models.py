import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Index, Float, Integer, ForeignKey, Boolean
from db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    google_id = Column(String, unique=True, nullable=True, index=True)
    google_calendar_token = Column(JSON, nullable=True)
    preferences = Column(JSON, nullable=True, default=dict)
    notification_preferences = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)


class Trip(Base):
    __tablename__ = "trips"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False)
    title = Column(String, nullable=False)
    status = Column(String, nullable=False, default="planning")
    raw_request = Column(JSON, nullable=True)
    plan = Column(JSON, nullable=True)
    # Full orchestrated state from LangGraph
    agent_state = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (Index("ix_trips_user_id", "user_id"),)


class TripFlight(Base):
    __tablename__ = "trip_flights"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_id = Column(String(36), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    provider_ref = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    price = Column(Float, nullable=True)
    currency = Column(String(10), nullable=True, default="USD")
    booked_at = Column(DateTime, nullable=True)

    __table_args__ = (Index("ix_trip_flights_trip_id", "trip_id"),)


class TripHotel(Base):
    __tablename__ = "trip_hotels"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_id = Column(String(36), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    provider_ref = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    price = Column(Float, nullable=True)
    currency = Column(String(10), nullable=True, default="USD")
    booked_at = Column(DateTime, nullable=True)

    __table_args__ = (Index("ix_trip_hotels_trip_id", "trip_id"),)


class ItineraryDay(Base):
    __tablename__ = "itinerary_days"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_id = Column(String(36), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    day_index = Column(Integer, nullable=False)
    date = Column(String(10), nullable=True)
    activities = Column(JSON, nullable=True)

    __table_args__ = (Index("ix_itinerary_days_trip_id", "trip_id"),)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_id = Column(String(36), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), nullable=False)
    type = Column(String(50), nullable=False)
    scheduled_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    is_sent = Column(Boolean, default=False)
    payload = Column(JSON, nullable=True)

    __table_args__ = (Index("ix_notifications_trip_id", "trip_id"),)
