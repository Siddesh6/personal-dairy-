import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "LifeMovie AI Backend"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:5432/lifemovie")
    
    # Redis & Celery
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week
    
    # AI API Keys (Optional defaults)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    RUNWAY_API_KEY: str = os.getenv("RUNWAY_API_KEY", "")
    ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
    SUNO_API_KEY: str = os.getenv("SUNO_API_KEY", "")
    
    # Auth0 Authentication Config
    AUTH0_DOMAIN: str = os.getenv("AUTH0_DOMAIN", "dev-lifemovie.us.auth0.com")
    AUTH0_AUDIENCE: str = os.getenv("AUTH0_AUDIENCE", "http://127.0.0.1:8000/api")
    
    class Config:
        case_sensitive = True

settings = Settings()
