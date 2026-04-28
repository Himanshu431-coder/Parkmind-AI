from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from app.db.database import init_db
from app.db.models import create_tables
from app.api.routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting ParkMind...")
    await init_db()
    await create_tables()
    print("All systems ready.")
    yield

app = FastAPI(title="ParkMind", description="AI Parking Pricing Engine", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(router, prefix="/api/v1", tags=["pricing"])

@app.get("/")
async def root():
    return FileResponse("dashboard.html")
