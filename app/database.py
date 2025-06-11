# sentra/app/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import settings

SQLALCHEMY_DATABASE_URL = settings.DB_URL

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ✅ Add this function for dependency injection in routes and testing
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
