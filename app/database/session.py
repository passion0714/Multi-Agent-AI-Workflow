from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv
from contextlib import contextmanager
from loguru import logger

load_dotenv()

# Database connection parameters
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "lead_processing")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Create database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create database engine
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=False,
)

# Create session factory
SessionFactory = sessionmaker(bind=engine)

# Create thread-safe scoped session
Session = scoped_session(SessionFactory)


@contextmanager
def get_db_session():
    """
    Context manager for database sessions.
    
    Usage:
    ------
    with get_db_session() as session:
        # Use session here
        results = session.query(SomeModel).all()
    
    # Session is automatically closed after the block
    """
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        session.close()


def get_engine():
    """
    Returns the SQLAlchemy engine instance.
    
    This is useful for direct engine operations and database migrations.
    """
    return engine 