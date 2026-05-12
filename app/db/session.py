from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection with pgAdmin settings
# Default: localhost:5433, database: postgres, user: postgres
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5433/postgres"
)

# Create engine with pool configuration for better performance
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    echo=False  # Set to True for SQL debugging
)

SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()