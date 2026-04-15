from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Ensure SQLAlchemy uses the psycopg driver
if DATABASE_URL:
    # Normalize any postgresql:// URL to use psycopg driver
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
    elif DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)

# Create engine with error handling
try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        connect_args={
            "connect_timeout": 10,
            "prepare_threshold": None
        },
    )
except Exception as e:
    print(f"⚠️  Error creating database engine: {e}")
    engine = None

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None
Base = declarative_base()


def get_db():
    """Dependency that provides a database session per request."""
    if not engine or not SessionLocal:
        raise RuntimeError("Database connection not configured. Check DATABASE_URL in .env")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
