"""
Proves the concurrency guarantee, not just claims it.

Fires N simultaneous check-in requests at a garage with M free EV spots and
asserts:
  - exactly M succeed and (N - M) fail with NoSpotAvailable
  - no spot is ever assigned to two tickets (the DB unique index enforces
    this; here we just confirm the app-level behaviour matches)

Requires a real Postgres reachable via DATABASE_URL (partial unique indexes
and FOR UPDATE SKIP LOCKED aren't meaningfully testable on SQLite). Run with:

    docker compose up -d db
    DATABASE_URL=postgresql://parking:parking@localhost:5432/parking pytest tests/test_concurrency.py
"""

import os
import threading

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import crud, models
from app.database import Base

DATABASE_URL = os.getenv("DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DATABASE_URL, reason="set DATABASE_URL to a running Postgres to run this test"
)


@pytest.fixture()
def db_session_factory():
    engine = create_engine(DATABASE_URL)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)

    session = Session()
    garage = models.Garage(id=1, name="Test Garage")
    session.add(garage)
    session.flush()

    NUM_SPOTS = 10
    for i in range(NUM_SPOTS):
        session.add(models.Spot(garage_id=1, floor=1, type=models.SpotType.EV))
    session.add(
        models.RateCard(
            vehicle_type=models.SpotType.EV,
            first_hour_rate=5,
            extra_hour_rate=3,
            daily_cap=20,
        )
    )
    session.commit()
    session.close()

    yield Session, NUM_SPOTS


def test_concurrent_checkins_never_overbook(db_session_factory):
    Session, num_spots = db_session_factory
    num_requests = 25

    results = {"success": 0, "no_spot": 0, "error": 0}
    lock = threading.Lock()

    def attempt(i):
        session = Session()
        try:
            crud.check_in(session, f"PLATE-{i}", models.SpotType.EV, garage_id=1)
            with lock:
                results["success"] += 1
        except crud.NoSpotAvailable:
            with lock:
                results["no_spot"] += 1
        except Exception:
            with lock:
                results["error"] += 1
        finally:
            session.close()

    threads = [threading.Thread(target=attempt, args=(i,)) for i in range(num_requests)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results["error"] == 0
    assert results["success"] == num_spots
    assert results["no_spot"] == num_requests - num_spots

    # Confirm the DB agrees: exactly num_spots occupied, zero free.
    session = Session()
    occupied = (
        session.query(models.Spot)
        .filter_by(garage_id=1, status=models.SpotStatus.OCCUPIED)
        .count()
    )
    assert occupied == num_spots
    session.close()
