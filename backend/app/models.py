import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Numeric,
    Boolean,
    Index,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from .database import Base


class SpotType(str, enum.Enum):
    COMPACT = "COMPACT"
    STANDARD = "STANDARD"
    EV = "EV"


class SpotStatus(str, enum.Enum):
    FREE = "FREE"
    OCCUPIED = "OCCUPIED"


class TicketStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


class Garage(Base):
    __tablename__ = "garages"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    spots = relationship("Spot", back_populates="garage")


class Spot(Base):
    __tablename__ = "spots"

    id = Column(Integer, primary_key=True)
    garage_id = Column(Integer, ForeignKey("garages.id"), nullable=False)
    floor = Column(Integer, nullable=False)
    type = Column(SAEnum(SpotType), nullable=False)
    status = Column(SAEnum(SpotStatus), nullable=False, default=SpotStatus.FREE)
    has_charger = Column(Boolean, default=False)

    garage = relationship("Garage", back_populates="spots")

    __table_args__ = (
        Index("idx_spots_garage_type_status", "garage_id", "type", "status"),
    )


class RateCard(Base):
    __tablename__ = "rate_cards"

    vehicle_type = Column(SAEnum(SpotType), primary_key=True)
    first_hour_rate = Column(Numeric(10, 2), nullable=False)
    extra_hour_rate = Column(Numeric(10, 2), nullable=False)
    daily_cap = Column(Numeric(10, 2), nullable=False)


class WaitlistEntry(Base):
    """
    A driver waiting for a spot type that's currently full. FIFO per
    (garage_id, vehicle_type). Fulfilled automatically the moment a matching
    spot is freed (see crud.check_out) and pushed to clients over the
    /ws/occupancy WebSocket.
    """

    __tablename__ = "waitlist"

    id = Column(Integer, primary_key=True)
    garage_id = Column(Integer, ForeignKey("garages.id"), nullable=False)
    plate = Column(String(20), nullable=False)
    vehicle_type = Column(SAEnum(SpotType), nullable=False)
    requested_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    fulfilled = Column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index("idx_waitlist_garage_type_open", "garage_id", "vehicle_type", "fulfilled"),
    )


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True)
    plate = Column(String(20), nullable=False)
    vehicle_type = Column(SAEnum(SpotType), nullable=False)
    spot_id = Column(Integer, ForeignKey("spots.id"), nullable=True)
    entry_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    exit_time = Column(DateTime, nullable=True)
    fee = Column(Numeric(10, 2), nullable=True)
    status = Column(SAEnum(TicketStatus), nullable=False, default=TicketStatus.ACTIVE)
    idempotency_key = Column(String(64), nullable=True)

    __table_args__ = (
        # The line that actually prevents double-parking: the DB rejects a
        # second active ticket on the same spot even under a race condition.
        Index(
            "one_active_ticket_per_spot",
            "spot_id",
            unique=True,
            postgresql_where=(status == TicketStatus.ACTIVE),
        ),
        # Fast plate lookup, scoped to active tickets only.
        Index(
            "idx_tickets_plate_active",
            "plate",
            postgresql_where=(status == TicketStatus.ACTIVE),
        ),
        # Idempotent check-in: a retried request with the same key never
        # creates a second ticket.
        Index(
            "idx_ticket_idempotency",
            "idempotency_key",
            unique=True,
            postgresql_where=(idempotency_key.isnot(None)),
        ),
    )
