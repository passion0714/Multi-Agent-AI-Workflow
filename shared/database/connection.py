"""
Database connection utilities for the Voice AI Agent system.

This module provides functions for establishing and managing database connections.
"""

import logging
from typing import Dict, Any
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session

from shared.config import get_db_config
from shared.logging_setup import setup_logging

# Configure logging
logger = setup_logging('database.connection')


# Global session factory to be initialized once
_SESSION_FACTORY = None
_ENGINE = None


def get_engine():
    """
    Get or create the SQLAlchemy engine.
    
    Returns:
        SQLAlchemy engine instance
    """
    global _ENGINE
    
    if _ENGINE is None:
        db_config = get_db_config()
        logger.info(f"Creating database engine with URL: {db_config['url']}")
        
        _ENGINE = create_engine(
            db_config['url'],
            pool_size=db_config['pool_size'],
            max_overflow=db_config['max_overflow'],
            pool_timeout=db_config['pool_timeout'],
            pool_recycle=db_config['pool_recycle']
        )
        
        logger.info("Database engine created successfully")
    
    return _ENGINE


def initialize_session_factory():
    """Initialize the global session factory."""
    global _SESSION_FACTORY
    
    if _SESSION_FACTORY is None:
        engine = get_engine()
        _SESSION_FACTORY = scoped_session(sessionmaker(bind=engine))
        logger.info("Database session factory initialized")


def get_db_session() -> Session:
    """
    Get a new database session.
    
    Returns:
        SQLAlchemy session object
    """
    if _SESSION_FACTORY is None:
        initialize_session_factory()
    
    return _SESSION_FACTORY()


@contextmanager
def db_session():
    """
    Context manager for database sessions.
    
    Automatically handles commit, rollback, and closing the session.
    
    Example:
        with db_session() as session:
            session.add(some_object)
    """
    session = get_db_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        session.close()


def close_all_sessions():
    """Close all database sessions."""
    if _SESSION_FACTORY is not None:
        _SESSION_FACTORY.remove()
        logger.info("All database sessions closed")


def healthcheck() -> Dict[str, Any]:
    """
    Perform a database health check.
    
    Returns:
        Dictionary with health check status
    """
    try:
        engine = get_engine()
        conn = engine.connect()
        conn.execute("SELECT 1")
        conn.close()
        return {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        } 