from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models
from .fee import compute_fee

# Vehicle -> ordered list of spot types it may use, first choice first.
# EV is mandatory-match (no fallback). Standard/compact fall back upward.
SPOT_FALLBACK = {
    models.SpotType.EV: [models.SpotType.EV],
    models.SpotType.STANDARD: [models.SpotType.STANDARD, models.SpotType.EV],
    models.SpotType.COMPACT: [
        models.SpotType.COMPACT,
        models.SpotType.STANDARD,
        models.SpotType.EV,
    ],
}


class NoSpotAvailable(Exception):
    pass


class DuplicateRequest(Exception):
    """Raised when an idempotency key has already been used."""

    def __init__(self, ticket: models.Ticket):
        self.ticket = ticket


class TicketNotFound(Exception):
    pass


def check_in(
    db: Session,
    plate: str,
    vehicle_type: models.SpotType,
    garage_id: int,
    idempotency_key: Optional[str] = None,
) -> models.Ticket:
    if idempotency_key:
        existing = (
            db.query(models.Ticket)
            .filter_by(idempotency_key=idempotency_key)
            .first()
        )
        if existing:
            raise DuplicateRequest(existing)

    spot = None
    for candidate_type in SPOT_FALLBACK[vehicle_type]:
        spot = (
            db.query(models.Spot)
            .filter(
                models.Spot.garage_id == garage_id,
                models.Spot.type == candidate_type,
                models.Spot.status == models.SpotStatus.FREE,
            )
            # Nearest-spot heuristic: lowest floor first.
            .order_by(models.Spot.floor.asc())
            # Locks the row; concurrent transactions skip it instead of
            # blocking or double-assigning it.
            .with_for_update(skip_locked=True)
            .first()
        )
        if spot:
            break

    if spot is None:
        raise NoSpotAvailable()

    spot.status = models.SpotStatus.OCCUPIED
    ticket = models.Ticket(
        plate=plate,
        vehicle_type=vehicle_type,
        spot_id=spot.id,
        entry_time=datetime.utcnow(),
        status=models.TicketStatus.ACTIVE,
        idempotency_key=idempotency_key,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def check_out(db: Session, ticket_id: int) -> Tuple[models.Ticket, Optional[models.WaitlistEntry]]:
    ticket = (
        db.query(models.Ticket)
        .filter_by(id=ticket_id, status=models.TicketStatus.ACTIVE)
        .with_for_update()
        .first()
    )
    if not ticket:
        raise TicketNotFound()

    rate = db.query(models.RateCard).filter_by(vehicle_type=ticket.vehicle_type).first()
    exit_time = datetime.utcnow()
    fee = compute_fee(
        ticket.entry_time,
        exit_time,
        rate.first_hour_rate,
        rate.extra_hour_rate,
        rate.daily_cap,
    )

    ticket.exit_time = exit_time
    ticket.fee = fee
    ticket.status = models.TicketStatus.CLOSED

    spot = db.query(models.Spot).filter_by(id=ticket.spot_id).first()
    notified: Optional[models.WaitlistEntry] = None
    if spot:
        spot.status = models.SpotStatus.FREE
        # Notify-on-availability: the moment this spot frees, hand it to
        # whoever's been waiting longest for this exact spot type.
        notified = (
            db.query(models.WaitlistEntry)
            .filter_by(garage_id=spot.garage_id, vehicle_type=spot.type, fulfilled=False)
            .order_by(models.WaitlistEntry.requested_at.asc())
            .with_for_update(skip_locked=True)
            .first()
        )
        if notified:
            notified.fulfilled = True

    db.commit()
    db.refresh(ticket)
    return ticket, notified


def join_waitlist(
    db: Session, plate: str, vehicle_type: models.SpotType, garage_id: int
) -> models.WaitlistEntry:
    entry = models.WaitlistEntry(
        plate=plate, vehicle_type=vehicle_type, garage_id=garage_id
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def analytics_summary(db: Session, garage_id: int) -> dict:
    """
    Cheap, index-backed aggregates a manager would actually check during
    the day: today's revenue, average stay length, and where the garage is
    full right now. No pre-aggregation table needed at this scale — these
    queries ride the same indexes check-in/out already rely on.
    """
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    revenue_today = (
        db.query(func.coalesce(func.sum(models.Ticket.fee), 0))
        .join(models.Spot, models.Ticket.spot_id == models.Spot.id)
        .filter(
            models.Spot.garage_id == garage_id,
            models.Ticket.status == models.TicketStatus.CLOSED,
            models.Ticket.exit_time >= today_start,
        )
        .scalar()
    )

    avg_dwell_minutes = (
        db.query(
            func.avg(
                func.extract("epoch", models.Ticket.exit_time - models.Ticket.entry_time)
                / 60
            )
        )
        .join(models.Spot, models.Ticket.spot_id == models.Spot.id)
        .filter(
            models.Spot.garage_id == garage_id,
            models.Ticket.status == models.TicketStatus.CLOSED,
            models.Ticket.exit_time >= today_start,
        )
        .scalar()
    )

    occupancy_by_floor = dict(
        db.query(models.Spot.floor, func.count(models.Spot.id))
        .filter(
            models.Spot.garage_id == garage_id,
            models.Spot.status == models.SpotStatus.OCCUPIED,
        )
        .group_by(models.Spot.floor)
        .all()
    )

    return {
        "revenue_today": float(revenue_today or 0),
        "avg_dwell_minutes": round(float(avg_dwell_minutes), 1) if avg_dwell_minutes else 0.0,
        "occupancy_by_floor": occupancy_by_floor,
    }


def search_by_plate(db: Session, plate: str) -> Optional[models.Ticket]:
    return (
        db.query(models.Ticket)
        .filter_by(plate=plate, status=models.TicketStatus.ACTIVE)
        .first()
    )


def availability(
    db: Session, garage_id: int, spot_type: Optional[models.SpotType] = None
) -> dict:
    base = db.query(models.Spot).filter(
        models.Spot.garage_id == garage_id,
        models.Spot.status == models.SpotStatus.FREE,
    )
    if spot_type:
        return {spot_type.value: base.filter(models.Spot.type == spot_type).count()}
    return {t.value: base.filter(models.Spot.type == t).count() for t in models.SpotType}
