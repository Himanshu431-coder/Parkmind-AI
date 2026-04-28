from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy import select, func
from app.db.database import get_db
from app.db.models import PriceHistory
from app.pricing.engine import pricing_engine
from app.services.rag_service import rag_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

class ParkingStateInput(BaseModel):
    lot_id: int
    timestamp: str
    occupancy: int
    capacity: int
    queue_length: int
    traffic_level: str
    is_special_day: bool = False
    vehicle_type: str = "car"
    latitude: float = 0.0
    longitude: float = 0.0
    use_rl: bool = True

class PriceResponse(BaseModel):
    lot_id: int
    suggested_price: float
    demand_score: float
    model_used: str
    cached: bool = False

class ModelCompareResponse(BaseModel):
    rl_price: float
    rl_model: str
    heuristic_price: float
    heuristic_model: str
    price_difference: float

class ChatInput(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    source: str

@router.post("/price", response_model=PriceResponse)
async def calculate_price(state: ParkingStateInput, db: AsyncSession = Depends(get_db)):
    ts = datetime.fromisoformat(state.timestamp)
    price, demand, model = pricing_engine.compute_price(occupancy=state.occupancy, capacity=state.capacity, queue_length=state.queue_length, traffic_level=state.traffic_level, is_special_day=state.is_special_day, vehicle_type=state.vehicle_type, hour=ts.hour, day_of_week=ts.weekday(), use_rl=state.use_rl)
    record = PriceHistory(lot_id=state.lot_id, timestamp=ts, occupancy=state.occupancy, capacity=state.capacity, queue_length=state.queue_length, traffic_level=state.traffic_level, is_special_day=state.is_special_day, vehicle_type=state.vehicle_type, latitude=state.latitude, longitude=state.longitude, suggested_price=price, demand_score=demand, model_used=model)
    db.add(record)
    await db.commit()
    return PriceResponse(lot_id=state.lot_id, suggested_price=price, demand_score=demand, model_used=model, cached=False)

@router.post("/compare", response_model=ModelCompareResponse)
async def compare_models(state: ParkingStateInput):
    ts = datetime.fromisoformat(state.timestamp)
    rl_price, _, rl_model = pricing_engine.compute_price(occupancy=state.occupancy, capacity=state.capacity, queue_length=state.queue_length, traffic_level=state.traffic_level, is_special_day=state.is_special_day, vehicle_type=state.vehicle_type, hour=ts.hour, day_of_week=ts.weekday(), use_rl=True)
    h_price, _, h_model = pricing_engine.compute_price(occupancy=state.occupancy, capacity=state.capacity, queue_length=state.queue_length, traffic_level=state.traffic_level, is_special_day=state.is_special_day, vehicle_type=state.vehicle_type, hour=ts.hour, day_of_week=ts.weekday(), use_rl=False)
    return ModelCompareResponse(rl_price=rl_price, rl_model=rl_model, heuristic_price=h_price, heuristic_model=h_model, price_difference=round(rl_price - h_price, 2))

@router.post("/chat", response_model=ChatResponse)
async def ai_chat(chat_input: ChatInput, db: AsyncSession = Depends(get_db)):
    pricing_data = await _get_pricing_context(db)
    answer = await rag_service.answer(chat_input.question, pricing_data)
    source = "groq_llama3" if rag_service.ready else "fallback"
    return ChatResponse(answer=answer, source=source)

async def _get_pricing_context(db: AsyncSession):
    result = await db.execute(select(PriceHistory).order_by(PriceHistory.created_at.desc()).limit(28))
    recent = result.scalars().all()
    total_result = await db.execute(select(func.count(PriceHistory.id)))
    total_records = total_result.scalar() or 0
    lots = []
    seen = set()
    for r in recent:
        if r.lot_id not in seen:
            seen.add(r.lot_id)
            lots.append({"lot_id": r.lot_id, "name": "BHMBCCMKT" + str(r.lot_id).zfill(2), "rl_price": r.suggested_price, "heuristic_price": r.suggested_price, "occupancy": r.occupancy, "capacity": r.capacity, "occupancy_rate": r.occupancy / max(r.capacity, 1), "queue_length": r.queue_length, "traffic_level": r.traffic_level, "is_special_day": r.is_special_day, "vehicle_type": r.vehicle_type, "demand_score": r.demand_score})
    avg_rl = sum(l["rl_price"] for l in lots) / max(len(lots), 1)
    avg_h = sum(l["heuristic_price"] for l in lots) / max(len(lots), 1)
    eff = ((avg_rl - avg_h) / max(avg_h, 0.01)) * 100
    most_exp = max(lots, key=lambda x: x["rl_price"]) if lots else {}
    cheapest = min(lots, key=lambda x: x["rl_price"]) if lots else {}
    return {"lots": lots, "summary": {"total_lots": 14, "avg_rl_price": avg_rl, "avg_heuristic_price": avg_h, "rl_efficiency": ("+" if eff > 0 else "") + str(round(eff,1)) + "%", "most_expensive": str(most_exp.get("name","N/A")) + " ($" + str(round(most_exp.get("rl_price",0),2)) + ")", "cheapest": str(cheapest.get("name","N/A")) + " ($" + str(round(cheapest.get("rl_price",0),2)) + ")", "total_records": total_records}}

@router.get("/health")
async def health_check():
    db_status = "unknown"
    try:
        from app.db.database import engine
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = "unhealthy"
    return {"status": "ok" if db_status == "healthy" else "degraded", "database": db_status, "cache": "active", "rl_agent": "loaded" if pricing_engine.rl_loaded else "not_loaded", "ai_chat": "groq" if rag_service.ready else "fallback"}
