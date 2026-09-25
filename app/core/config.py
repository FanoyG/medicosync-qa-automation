from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_PATH = Path(__file__).resolve().parents[2] / ".env"

class Settings(BaseSettings):
    
    PROJECT_NAME: str = "MedicoSync"

    # Database
    DATABASE_URL: str = Field(alias="DATABASE_URL", description="Alembic Connection")  # e.g., Alembic 
    DB_CONNECTION: str = Field(alias="DB_CONNECTION", description="Fastapi Connection") # e.g., "postgresql://user:password@localhost/medicosync"
    REDIS_URL: str = Field(alias="REDIS_URL", description="Redis connection")

    # Security
    SECRET_KEY: str = Field(alias="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    MAX_VERIFY_ATTEMPTS: int = 3

    model_config = SettingsConfigDict(env_file=ENV_PATH, extra="ignore")

settings = Settings() #type: ignore
