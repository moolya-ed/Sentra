from pydantic import BaseSettings

class Settings(BaseSettings):
    DB_URL: str = "sqlite:///./data/sentra.db"
    LOG_LEVEL: str = "info"
    SPIKE_THRESHOLD: int = 100
    BLOCK_DURATION_MINUTES: int = 60

    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    ALERT_RECEIVER: str

    class Config:
        env_file = ".env"

settings = Settings()

SPIKE_THRESHOLD = settings.SPIKE_THRESHOLD
BLOCK_DURATION_MINUTES = settings.BLOCK_DURATION_MINUTES

SMTP_HOST = settings.SMTP_HOST
SMTP_PORT = settings.SMTP_PORT
SMTP_USER = settings.SMTP_USER
SMTP_PASSWORD = settings.SMTP_PASSWORD
ALERT_RECEIVER = settings.ALERT_RECEIVER
