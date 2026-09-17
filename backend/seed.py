"""
Seeds one garage with a mix of spot types and rate cards for all vehicle
types. Run after the API has created tables (or run create_all yourself):

    python seed.py
"""

from app.database import Base, SessionLocal, engine
from app import models

Base.metadata.create_all(bind=engine)
db = SessionLocal()

if not db.query(models.Garage).filter_by(id=1).first():
    db.add(models.Garage(id=1, name="Downtown Garage"))
    db.flush()

    # 3 floors: mostly standard, some compact, a handful of EV with chargers
    for floor in range(1, 4):
        for _ in range(10):
            db.add(models.Spot(garage_id=1, floor=floor, type=models.SpotType.STANDARD))
        for _ in range(5):
            db.add(models.Spot(garage_id=1, floor=floor, type=models.SpotType.COMPACT))
        for _ in range(2):
            db.add(
                models.Spot(
                    garage_id=1, floor=floor, type=models.SpotType.EV, has_charger=True
                )
            )

    db.add(
        models.RateCard(
            vehicle_type=models.SpotType.COMPACT,
            first_hour_rate=3,
            extra_hour_rate=2,
            daily_cap=15,
        )
    )
    db.add(
        models.RateCard(
            vehicle_type=models.SpotType.STANDARD,
            first_hour_rate=5,
            extra_hour_rate=3,
            daily_cap=20,
        )
    )
    db.add(
        models.RateCard(
            vehicle_type=models.SpotType.EV,
            first_hour_rate=6,
            extra_hour_rate=4,
            daily_cap=25,
        )
    )
    db.commit()
    print("Seeded garage 1 with 51 spots and rate cards.")
else:
    print("Garage 1 already exists, skipping seed.")

db.close()
