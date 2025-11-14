import os
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
from typing import Generator

logger = logging.getLogger("health_assistant")

# Get database URL from environment
DATABASE_URL = os.getenv("NEON_DB_URL")

if not DATABASE_URL:
    logger.warning("NEON_DB_URL not found in environment variables. Database features will be disabled.")
    engine = None
    SessionLocal = None
else:
    # Create engine with connection pooling
    # Neon requires SSL, so we need to add sslmode=require to the URL
    if DATABASE_URL.startswith("postgresql://"):
        # Replace postgresql:// with postgresql+psycopg2:// for SQLAlchemy
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
    
    # Add SSL requirement if not already present
    if "sslmode" not in DATABASE_URL:
        separator = "&" if "?" in DATABASE_URL else "?"
        DATABASE_URL = f"{DATABASE_URL}{separator}sslmode=require"
    
    try:
        engine = create_engine(
            DATABASE_URL,
            poolclass=NullPool,  # Neon works better with NullPool
            echo=False,  # Set to True for SQL query logging
            connect_args={
                "connect_timeout": 10,
            }
        )
        
        # Test connection
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        logger.info("Successfully connected to NeonDB")
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    except Exception as e:
        logger.error(f"Failed to connect to NeonDB: {e}")
        engine = None
        SessionLocal = None

Base = declarative_base()


class DatabaseClient:
    """Database client for NeonDB operations"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self.engine is not None and self.SessionLocal is not None
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup"""
        if not self.is_connected():
            raise Exception("Database not connected. Check NEON_DB_URL environment variable.")
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def create_tables(self):
        """Create all database tables"""
        if not self.is_connected():
            logger.warning("Cannot create tables: database not connected")
            return False
        
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test database connection"""
        if not self.is_connected():
            return False
        
        try:
            from sqlalchemy import text
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False


# Global database client instance
db_client = DatabaseClient()


def init_db():
    """Initialize database - create tables if they don't exist"""
    if db_client.is_connected():
        db_client.create_tables()
    else:
        logger.warning("Database initialization skipped: not connected")

