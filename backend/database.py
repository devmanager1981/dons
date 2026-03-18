"""
Database configuration and connection management for DONS platform.
"""
import os
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool, StaticPool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL configuration
DATABASE_URL = os.getenv("DATABASE_URL")

# For production, use PostgreSQL with SSL
if not DATABASE_URL:
    POSTGRES_USER = os.getenv("POSTGRES_DB_USERNAME", "doadmin")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_DB_PWD")
    POSTGRES_HOST = os.getenv("POSTGRES_DB_HOST")
    POSTGRES_PORT = os.getenv("POSTGRES_DB_PORT", "25060")
    POSTGRES_DB = os.getenv("POSTGRES_DB_database", "defaultdb")
    POSTGRES_SSLMODE = os.getenv("POSTGRES_SSLMODE", "require")
    
    if all([POSTGRES_PASSWORD, POSTGRES_HOST]):
        DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}?sslmode={POSTGRES_SSLMODE}"

# Fallback to SQLite for local development if no valid DATABASE_URL
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./dons_local.db"
    print("[INFO] No DATABASE_URL set, using local SQLite: dons_local.db")

# Create engine with appropriate settings
if DATABASE_URL.startswith("sqlite"):
    # SQLite needs special handling
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
else:
    # PostgreSQL with connection pooling
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=False
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency function to get database session.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_health() -> bool:
    """
    Check if database connection is healthy.
    
    Returns:
        bool: True if database is accessible, False otherwise
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database health check failed: {e}")
        return False


def init_db():
    """
    Initialize database by creating all tables.
    Should be called on application startup.
    """
    from models import User, InfrastructureUpload, MigrationPlan, Deployment, Alert, AIRecommendation, SelfHealingAction, Document, DocumentChunk
    Base.metadata.create_all(bind=engine)
