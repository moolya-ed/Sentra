# sentra/app/config.py

from pydantic import BaseSettings

class Settings(BaseSettings):
    DB_URL: str = "sqlite:///./data/sentra.db"
    LOG_LEVEL: str = "info"

    class Config:
        env_file = ".env"

settings = Settings()
