from typing import List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import Base, engine, get_db

app = FastAPI(title="Parking Garage API")

# Dev-friendly CORS: the React app runs on a different port (5173) than the
# API (8000). Lock this down to your real frontend origin in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# For a first run without a migrations tool, create tables directly.
# Swap this for Alembic once the schema stabilizes.
Base.metadata.create_all(bind=engine)


# ---- Live occupancy broadcast (WebSocket) -------------------------------


class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, message: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


@app.websocket("/ws/occupancy")
async def occupancy_ws(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # This channel is broadcast-only; just keep the connection open.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ---- REST endpoints -------------------------------------------------------


@app.post("/checkin", response_model=schemas.TicketResponse)
async def checkin(
    body: schemas.CheckInRequest,
    db: Session = Depends(get_db),
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
):
    try:
        ticket = crud.check_in(
            db, body.plate, body.vehicle_type, body.garage_id, idempotency_key
        )
    except crud.DuplicateRequest as e:
        return e.ticket
    except crud.NoSpotAvailable:
        raise HTTPException(status_code=409, detail="No matching spot available")

    await manager.broadcast(
        {"event": "spot_occupied", "spot_id": ticket.spot_id, "garage_id": body.garage_id}
    )
    return ticket


@app.post("/checkout/{ticket_id}", response_model=schemas.TicketResponse)
async def checkout(ticket_id: int, db: Session = Depends(get_db)):
    try:
        ticket, notified = crud.check_out(db, ticket_id)
    except crud.TicketNotFound:
        raise HTTPException(status_code=404, detail="No active ticket found")

    await manager.broadcast({"event": "spot_freed", "spot_id": ticket.spot_id})

    if notified:
        # Notify-on-availability: pushed to every connected client; the
        # frontend filters by plate to show the right driver their alert.
        await manager.broadcast(
            {
                "event": "waitlist_spot_ready",
                "plate": notified.plate,
                "garage_id": notified.garage_id,
                "spot_type": notified.vehicle_type.value,
            }
        )

    return ticket


@app.post("/waitlist/join", response_model=schemas.WaitlistResponse)
def join_waitlist(body: schemas.WaitlistRequest, db: Session = Depends(get_db)):
    entry = crud.join_waitlist(db, body.plate, body.vehicle_type, body.garage_id)
    return entry


@app.get("/analytics/summary")
def analytics_summary(garage_id: int, db: Session = Depends(get_db)):
    return crud.analytics_summary(db, garage_id)


@app.get("/tickets/search", response_model=schemas.TicketResponse)
def search(plate: str = Query(...), db: Session = Depends(get_db)):
    ticket = crud.search_by_plate(db, plate)
    if not ticket:
        raise HTTPException(status_code=404, detail="No active ticket for that plate")
    return ticket


@app.get("/availability", response_model=schemas.AvailabilityResponse)
def get_availability(
    garage_id: int,
    type: Optional[models.SpotType] = None,
    db: Session = Depends(get_db),
):
    counts = crud.availability(db, garage_id, type)
    return {"garage_id": garage_id, "counts": counts}


@app.get("/tickets", response_model=List[schemas.TicketResponse])
def list_tickets(
    status: Optional[models.TicketStatus] = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(models.Ticket)
    if status:
        q = q.filter(models.Ticket.status == status)
    q = q.order_by(models.Ticket.entry_time.desc())
    return q.offset((page - 1) * page_size).limit(page_size).all()
