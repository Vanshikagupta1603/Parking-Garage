"""
Proves the notify-on-availability queue actually behaves FIFO: the driver
who's been waiting longest for a given spot type gets matched first when
one frees up. Requires Postgres (see test_concurrency.py for why).
"""

import os

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
    session.add(models.Garage(id=1, name="Test Garage"))
    session.flush()
    # Exactly one EV spot, already occupied, so the garage is full.
    session.add(models.Spot(id=1, garage_id=1, floor=1, type=models.SpotType.EV,
                             status=models.SpotStatus.OCCUPIED))
    session.add(models.Ticket(id=1, plate="OCCUPANT", vehicle_type=models.SpotType.EV,
                               spot_id=1, status=models.TicketStatus.ACTIVE))
    session.add(models.RateCard(vehicle_type=models.SpotType.EV, first_hour_rate=6,
                                 extra_hour_rate=4, daily_cap=25))
    session.commit()
    session.close()

    yield Session


def test_waitlist_fulfilled_fifo_on_checkout(db_session_factory):
    Session = db_session_factory
    session = Session()

    # Two drivers queue for the one EV spot, in this order.
    first = crud.join_waitlist(session, "FIRST-IN-LINE", models.SpotType.EV, garage_id=1)
    second = crud.join_waitlist(session, "SECOND-IN-LINE", models.SpotType.EV, garage_id=1)
    assert not first.fulfilled and not second.fulfilled

    # The occupant checks out, freeing the only EV spot.
    ticket, notified = crud.check_out(session, ticket_id=1)

    assert notified is not None
    assert notified.plate == "FIRST-IN-LINE"

    session.refresh(first)
    session.refresh(second)
    assert first.fulfilled is True
    assert second.fulfilled is False  # still waiting — only one spot freed

    session.close()
