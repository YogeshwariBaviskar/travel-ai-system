"""Add trip detail tables: trip_flights, trip_hotels, itinerary_days, notifications.
   Also add agent_state, updated_at to trips and extend users.

Revision ID: 002
Revises: 001
Create Date: 2026-05-06
"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extend users table
    op.add_column("users", sa.Column("google_calendar_token", sa.JSON(), nullable=True))
    op.add_column("users", sa.Column("notification_preferences", sa.JSON(), nullable=True))

    # Extend trips table
    op.add_column("trips", sa.Column("agent_state", sa.JSON(), nullable=True))
    op.add_column("trips", sa.Column("updated_at", sa.DateTime(), nullable=True))

    op.create_table(
        "trip_flights",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("trip_id", sa.String(36), sa.ForeignKey("trips.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider_ref", sa.String(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("price", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(10), nullable=True),
        sa.Column("booked_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_trip_flights_trip_id", "trip_flights", ["trip_id"])

    op.create_table(
        "trip_hotels",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("trip_id", sa.String(36), sa.ForeignKey("trips.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider_ref", sa.String(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("price", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(10), nullable=True),
        sa.Column("booked_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_trip_hotels_trip_id", "trip_hotels", ["trip_id"])

    op.create_table(
        "itinerary_days",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("trip_id", sa.String(36), sa.ForeignKey("trips.id", ondelete="CASCADE"), nullable=False),
        sa.Column("day_index", sa.Integer(), nullable=False),
        sa.Column("date", sa.String(10), nullable=True),
        sa.Column("activities", sa.JSON(), nullable=True),
    )
    op.create_index("ix_itinerary_days_trip_id", "itinerary_days", ["trip_id"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("trip_id", sa.String(36), sa.ForeignKey("trips.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("is_sent", sa.Boolean(), default=False),
        sa.Column("payload", sa.JSON(), nullable=True),
    )
    op.create_index("ix_notifications_trip_id", "notifications", ["trip_id"])


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("itinerary_days")
    op.drop_table("trip_hotels")
    op.drop_table("trip_flights")
    op.drop_column("trips", "updated_at")
    op.drop_column("trips", "agent_state")
    op.drop_column("users", "notification_preferences")
    op.drop_column("users", "google_calendar_token")
