"""
Database setup script for initializing the shared data store.
"""

import os
import sys
import argparse
from pathlib import Path

# Add the parent directory to the module search path
sys.path.append(str(Path(__file__).parent.parent))

from database.models import init_db, get_engine, get_session, Base, Lead, LeadStatus
from shared import config
from shared.logging_setup import setup_logging, setup_stdlib_logging

# Set up logging
logger = setup_logging("database_setup")
setup_stdlib_logging()

def create_database():
    """Initialize the database and create tables"""
    logger.info("Creating database tables...")
    
    try:
        engine = init_db()
        logger.info(f"Database initialized successfully at {config.DATABASE_URL}")
        
        # If we're using SQLite, make sure the directory exists
        if config.DATABASE_URL.startswith('sqlite:///'):
            # Extract the path part from the URL
            path = config.DATABASE_URL[10:]
            directory = os.path.dirname(path)
            
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                logger.info(f"Created directory for SQLite database: {directory}")
        
        return engine
    
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise

def check_database_connection():
    """Test the database connection"""
    try:
        engine = get_engine()
        connection = engine.connect()
        connection.close()
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return False

def create_sample_data(num_leads=5):
    """Create sample lead data for testing"""
    logger.info(f"Creating {num_leads} sample leads for testing...")
    
    try:
        session = get_session()
        
        # See if we already have leads
        existing_count = session.query(Lead).count()
        if existing_count > 0:
            logger.info(f"Found {existing_count} existing leads, skipping sample data creation")
            return
        
        # Sample data
        sample_leads = [
            {
                "name": "John Smith",
                "email": "john.smith@example.com",
                "phone": "+15551234567",
                "address": "123 Main St, Springfield, IL 62704",
                "area_of_interest": "Home Insurance",
                "tcpa_consent": False,
                "status": LeadStatus.PENDING,
                "source": "Sample Data"
            },
            {
                "name": "Jane Doe",
                "email": "jane.doe@example.com",
                "phone": "+15555678901",
                "address": "456 Oak Ave, Chicago, IL 60611",
                "area_of_interest": "Auto Insurance",
                "tcpa_consent": False,
                "status": LeadStatus.PENDING,
                "source": "Sample Data"
            },
            {
                "name": "Robert Johnson",
                "email": "robert.johnson@example.com",
                "phone": "+15552345678",
                "address": "789 Pine St, New York, NY 10001",
                "area_of_interest": "Life Insurance",
                "tcpa_consent": False,
                "status": LeadStatus.PENDING,
                "source": "Sample Data"
            },
            {
                "name": "Susan Williams",
                "email": "susan.williams@example.com",
                "phone": "+15553456789",
                "address": "321 Elm St, Los Angeles, CA 90001",
                "area_of_interest": "Health Insurance",
                "tcpa_consent": False,
                "status": LeadStatus.PENDING,
                "source": "Sample Data"
            },
            {
                "name": "Michael Brown",
                "email": "michael.brown@example.com",
                "phone": "+15554567890",
                "address": "654 Maple St, Dallas, TX 75201",
                "area_of_interest": "Business Insurance",
                "tcpa_consent": False,
                "status": LeadStatus.PENDING,
                "source": "Sample Data"
            }
        ]
        
        # Create leads
        for i, lead_data in enumerate(sample_leads):
            if i < num_leads:
                lead = Lead(**lead_data)
                session.add(lead)
                logger.debug(f"Added sample lead: {lead.name}")
        
        session.commit()
        logger.info(f"Successfully created {num_leads} sample leads")
    
    except Exception as e:
        logger.error(f"Error creating sample data: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()

def main():
    """Main function to set up the database"""
    parser = argparse.ArgumentParser(description="Initialize the Voice AI Agent database")
    parser.add_argument('--sample-data', action='store_true', 
                        help='Create sample data for testing')
    parser.add_argument('--num-leads', type=int, default=5,
                        help='Number of sample leads to create')
    parser.add_argument('--check-connection', action='store_true',
                        help='Test the database connection')
    
    args = parser.parse_args()
    
    if args.check_connection:
        success = check_database_connection()
        sys.exit(0 if success else 1)
    
    create_database()
    
    if args.sample_data:
        create_sample_data(args.num_leads)
    
    logger.info("Database setup complete")

if __name__ == "__main__":
    main() 