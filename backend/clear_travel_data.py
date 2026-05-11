"""One-off script to delete all travel entries (trips + cascading tables). Users are kept."""
import os
import sys

# Ensure backend modules are importable when run from repo root or backend/
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import text
from db.database import SessionLocal

TABLES = [
    "notifications",
    "itinerary_days",
    "trip_hotels",
    "trip_flights",
    "trips",
]


def clear_travel_data() -> None:
    db = SessionLocal()
    try:
        for table in TABLES:
            result = db.execute(text(f"DELETE FROM {table}"))
            print(f"Deleted {result.rowcount} rows from {table}")
        db.commit()
        print("Done.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    clear_travel_data()
