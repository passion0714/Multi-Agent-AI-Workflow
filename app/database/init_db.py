import os
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from app.database.models import Base
from app.database.session import engine
from loguru import logger
from dotenv import load_dotenv
import argparse

load_dotenv()


def init_db(drop_all=False):
    """
    Initialize the database by creating all tables defined in the models.
    
    Parameters:
    -----------
    drop_all : bool, optional
        If True, drop all existing tables before creating new ones.
        Default is False.
    """
    try:
        if drop_all:
            logger.info("Dropping all tables...")
            Base.metadata.drop_all(engine)
            logger.info("All tables dropped successfully.")
        
        logger.info("Creating database tables...")
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully.")
        
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Initialize the database for the multi-agent system")
    parser.add_argument("--drop", action="store_true", help="Drop all existing tables before creating new ones")
    args = parser.parse_args()
    
    # Configure logging
    log_file = os.getenv("LOG_FILE", "logs/db_init.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logger.add(log_file, rotation="10 MB", retention="7 days")
    
    logger.info("Starting database initialization...")
    
    success = init_db(drop_all=args.drop)
    
    if success:
        logger.info("Database initialization completed successfully.")
    else:
        logger.error("Database initialization failed.")
        sys.exit(1)


if __name__ == "__main__":
    main() 