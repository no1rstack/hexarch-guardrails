"""
Database connection and session management.
Supports both SQLite (local) and PostgreSQL (production).
"""

import os
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Database URL configuration
def get_database_url() -> str:
    """
    Determine database URL from environment or use SQLite default.
    
    Environment variables:
    - DATABASE_URL: Full connection string (e.g., postgresql://user:pass@host/db)
    - DATABASE_PROVIDER: 'sqlite' or 'postgresql' (default: 'sqlite')
    - DATABASE_PATH: Path for SQLite (default: './hexarch.db')
    """
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url
    
    provider = os.getenv("DATABASE_PROVIDER", "sqlite").lower()
    
    if provider == "postgresql":
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "")
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        database = os.getenv("DB_NAME", "hexarch")
        
        if password:
            return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
        else:
            return f"postgresql+psycopg2://{user}@{host}:{port}/{database}"
    
    else:  # sqlite
        db_path = os.getenv("DATABASE_PATH", "./hexarch.db")
        return f"sqlite:///{db_path}"


class DatabaseManager:
    """Manages database connection and session lifecycle."""
    
    _engine = None
    _session_factory = None
    
    @classmethod
    def initialize(cls, database_url: Optional[str] = None):
        """
        Initialize database engine and session factory.
        
        Args:
            database_url: Optional override for database URL
        """
        if cls._engine is not None:
            return
        
        if database_url is None:
            database_url = get_database_url()
        
        # Configure engine based on database type
        engine_kwargs = {}
        
        if "sqlite" in database_url:
            # SQLite configuration for local development
            engine_kwargs = {
                "echo": os.getenv("SQL_ECHO", "false").lower() == "true",
                "connect_args": {"check_same_thread": False},
                "poolclass": StaticPool,
            }
        else:
            # PostgreSQL configuration for production
            engine_kwargs = {
                "echo": os.getenv("SQL_ECHO", "false").lower() == "true",
                "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
                "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
            }
        
        cls._engine = create_engine(database_url, **engine_kwargs)
        cls._session_factory = sessionmaker(bind=cls._engine, expire_on_commit=False)
    
    @classmethod
    def get_session(cls) -> Session:
        """
        Get a new database session.
        
        Returns:
            SQLAlchemy Session instance
        """
        if cls._session_factory is None:
            cls.initialize()
        
        return cls._session_factory()
    
    @classmethod
    def get_engine(cls):
        """Get the database engine."""
        if cls._engine is None:
            cls.initialize()
        
        return cls._engine
    
    @classmethod
    def create_all(cls):
        """Create all tables in the database."""
        if cls._engine is None:
            cls.initialize()
        
        from hexarch_cli.models import Base
        Base.metadata.create_all(cls._engine)
    
    @classmethod
    def drop_all(cls):
        """Drop all tables from the database (DANGEROUS - use with caution)."""
        if cls._engine is None:
            cls.initialize()
        
        from hexarch_cli.models import Base
        Base.metadata.drop_all(cls._engine)
    
    @classmethod
    def close(cls):
        """Close database connections."""
        if cls._engine is not None:
            cls._engine.dispose()
            cls._engine = None
            cls._session_factory = None


def get_db_session() -> Session:
    """
    Convenience function to get a new database session.
    Useful for dependency injection in CLI commands.
    """
    return DatabaseManager.get_session()
