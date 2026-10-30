"""
Database engine configuration, connection handling, and session management.
Supports PostgreSQL (with pgvector) and includes robust fallback for local dev/testing.
"""

import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError

from backend.core.config import settings
from backend.database.models import Base

logger = logging.getLogger(__name__)

# State flags
IS_POSTGRES = False
PGVECTOR_AVAILABLE = False
ACTIVE_DATABASE_URL = ""


def get_db_engine():
    """
    Initializes and returns the SQLAlchemy engine.
    Tries PostgreSQL first; if unavailable, falls back to SQLite for zero-setup local dev/tests.
    """
    global IS_POSTGRES, PGVECTOR_AVAILABLE, ACTIVE_DATABASE_URL
    target_url = settings.DATABASE_URL

    # Test PostgreSQL connection if configured
    if target_url.startswith("postgresql"):
        try:
            logger.info("Attempting to connect to PostgreSQL at %s", target_url)
            engine = create_engine(
                target_url,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 2}
            )
            with engine.connect() as conn:
                conn.execute(text("SELECT 1;"))
            
            IS_POSTGRES = True
            ACTIVE_DATABASE_URL = target_url
            logger.info("Successfully connected to PostgreSQL database.")

            # Check / enable pgvector extension
            try:
                with engine.connect() as conn:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                    conn.commit()
                PGVECTOR_AVAILABLE = True
                logger.info("pgvector extension is enabled and available in PostgreSQL.")
            except Exception as e:
                PGVECTOR_AVAILABLE = False
                logger.warning(
                    "PostgreSQL connected, but pgvector extension is not available: %s. "
                    "Embeddings will be indexed using JSON vector storage with exact cosine retrieval.",
                    str(e)
                )

            return engine
        except (OperationalError, Exception) as exc:
            logger.warning(
                "Could not connect to PostgreSQL (%s). Falling back to local SQLite at %s for local development. "
                "To use PostgreSQL, start PostgreSQL service and update DATABASE_URL in .env.",
                str(exc),
                settings.SQLITE_FALLBACK_URL
            )
            target_url = settings.SQLITE_FALLBACK_URL

    # SQLite fallback
    IS_POSTGRES = False
    PGVECTOR_AVAILABLE = False
    ACTIVE_DATABASE_URL = target_url
    engine = create_engine(
        target_url,
        connect_args={"check_same_thread": False} if target_url.startswith("sqlite") else {}
    )
    return engine


engine = get_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """
    Create tables if they do not exist.
    """
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session and ensures clean closure.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def is_pgvector_active() -> bool:
    """Returns True if connected to PostgreSQL with pgvector enabled."""
    return PGVECTOR_AVAILABLE


def get_database_info() -> dict:
    """Returns current database diagnostics for health check and user info."""
    return {
        "engine": "PostgreSQL" if IS_POSTGRES else "SQLite (Local Fallback)",
        "pgvector_enabled": PGVECTOR_AVAILABLE,
        "database_url": ACTIVE_DATABASE_URL.split("@")[-1] if "@" in ACTIVE_DATABASE_URL else ACTIVE_DATABASE_URL
    }
