from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel

from .models import SpotType, TicketStatus


class CheckInRequest(BaseModel):
    plate: str
    vehicle_type: SpotType
    garage_id: int


class TicketResponse(BaseModel):
    id: int
    plate: str
    vehicle_type: SpotType
    spot_id: Optional[int]
    entry_time: datetime
    exit_time: Optional[datetime]
    fee: Optional[Decimal]
    status: TicketStatus

    class Config:
        from_attributes = True


class AvailabilityResponse(BaseModel):
    garage_id: int
    counts: dict


class WaitlistRequest(BaseModel):
    plate: str
    vehicle_type: SpotType
    garage_id: int


class WaitlistResponse(BaseModel):
    id: int
    plate: str
    vehicle_type: SpotType
    garage_id: int
    requested_at: datetime
    fulfilled: bool

    class Config:
        from_attributes = True
