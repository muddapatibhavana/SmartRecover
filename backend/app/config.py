import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    PROJECT_NAME: str = "SmartRecover"
    TAGLINE: str = "AI-powered payment recovery with safe stopping."
    API_PREFIX: str = os.getenv("API_PREFIX", "/api")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./smartrecover.db")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    APP_ENV: str = os.getenv("APP_ENV", "development")

settings = Settings()
