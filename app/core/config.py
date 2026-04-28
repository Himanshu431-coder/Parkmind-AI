from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./parking.db"
    BASE_PRICE: float = 10.0
    MIN_PRICE: float = 5.0
    MAX_PRICE: float = 20.0
    GROQ_API_KEY: str = ""
    model_config = {"env_file": ".env", "extra": "ignore"}

@lru_cache()
def get_settings():
    return Settings()
