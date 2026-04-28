from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class PriceHistory(Base):
    __tablename__ = "price_history"
    id = Column(Integer, primary_key=True, index=True)
    lot_id = Column(Integer, index=True)
    timestamp = Column(DateTime)
    occupancy = Column(Integer)
    capacity = Column(Integer)
    queue_length = Column(Integer)
    traffic_level = Column(String(20))
    is_special_day = Column(Boolean, default=False)
    vehicle_type = Column(String(20))
    latitude = Column(Float, default=0.0)
    longitude = Column(Float, default=0.0)
    suggested_price = Column(Float)
    demand_score = Column(Float)
    model_used = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())

async def create_tables():
    from app.db.database import engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully.")
