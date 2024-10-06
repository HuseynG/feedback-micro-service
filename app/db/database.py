# app/db/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings
from db.base import Base

# Create the engine using the DATABASE_URL from settings
engine = create_engine(settings.database_url, fast_executemany=True)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """
    Initializes the database by creating all tables defined in the models.
    """
    Base.metadata.create_all(bind=engine)
