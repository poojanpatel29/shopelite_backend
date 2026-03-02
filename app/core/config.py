from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):

    APP_NAME: str = "ShopElite API"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str
    DATABASE_MIGRATION_URL: str = ""
    
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    FRONTEND_URL: str = "http://localhost:5173"

    class Config:
        env_file = ".env"

settings = Settings()