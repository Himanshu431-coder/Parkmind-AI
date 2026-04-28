"""ParkMind API Tests - 8 automated tests."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

transport = ASGITransport(app=app)

@pytest.mark.asyncio
async def test_health_returns_200():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/api/v1/health")
    assert r.status_code == 200

@pytest.mark.asyncio
async def test_health_has_database():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/api/v1/health")
    data = r.json()
    assert "database" in data
    assert data["database"] in ["healthy", "unknown"]

@pytest.mark.asyncio
async def test_health_has_rl_agent_field():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/api/v1/health")
    data = r.json()
    assert "rl_agent" in data

@pytest.mark.asyncio
async def test_price_returns_200():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/api/v1/price", json={
            "lot_id": 1,
            "timestamp": "2025-07-07T14:30:00",
            "occupancy": 85,
            "capacity": 100,
            "queue_length": 12,
            "traffic_level": "high",
            "is_special_day": True,
            "vehicle_type": "car",
            "use_rl": True
        })
    assert r.status_code == 200

@pytest.mark.asyncio
async def test_price_has_required_fields():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/api/v1/price", json={
            "lot_id": 1,
            "timestamp": "2025-07-07T14:30:00",
            "occupancy": 85,
            "capacity": 100,
            "queue_length": 12,
            "traffic_level": "high",
            "is_special_day": False,
            "vehicle_type": "car",
            "use_rl": True
        })
    data = r.json()
    assert "suggested_price" in data
    assert "demand_score" in data
    assert "model_used" in data

@pytest.mark.asyncio
async def test_compare_returns_200():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/api/v1/compare", json={
            "lot_id": 1,
            "timestamp": "2025-07-07T14:30:00",
            "occupancy": 85,
            "capacity": 100,
            "queue_length": 12,
            "traffic_level": "high",
            "is_special_day": False,
            "vehicle_type": "car"
        })
    assert r.status_code == 200
    data = r.json()
    assert "rl_price" in data
    assert "heuristic_price" in data
    assert "price_difference" in data

@pytest.mark.asyncio
async def test_price_rejects_missing_fields():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/api/v1/price", json={
            "lot_id": 1
        })
    assert r.status_code == 422

@pytest.mark.asyncio
async def test_chat_returns_response():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/api/v1/chat", json={"question": "status"})
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert "source" in data
