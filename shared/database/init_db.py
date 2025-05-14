#!/usr/bin/env python3
"""
Database initialization script for the Voice AI Agent system.

This script creates all the necessary database tables and can seed
the database with initial data for development or testing purposes.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Add parent directory to path to allow imports from shared modules
parent_dir = Path(__file__).resolve().parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from shared.database.models import Base, engine, init_db, drop_db, get_session
from shared.database.models import Lead, LeadStatus, Call, CallStatus
from shared.logging_setup import setup_logging

# Configure logging
logger = setup_logging('init_db')


def create_tables():
    """Create all database tables."""
    logger.info("Creating database tables...")
    init_db()
    logger.info("Database tables created successfully.")


def drop_tables(confirm=False):
    """Drop all database tables."""
    if not confirm:
        logger.warning("This will delete all data in the database.")
        user_input = input("Are you sure you want to proceed? (y/n): ")
        if user_input.lower() != 'y':
            logger.info("Operation cancelled.")
            return False
    
    logger.info("Dropping database tables...")
    drop_db()
    logger.info("Database tables dropped successfully.")
    return True


def seed_test_data():
    """Seed the database with test data."""
    logger.info("Seeding database with test data...")
    session = get_session()
    
    try:
        # Create some test leads
        test_leads = [
            Lead(
                first_name="John",
                last_name="Doe",
                email="john.doe@example.com",
                phone="5551234567",
                address="123 Main St",
                city="Springfield",
                state="IL",
                zip_code="62701",
                status=LeadStatus.NEW,
                area_of_interest="Health Insurance",
                is_tcpa_compliant=True
            ),
            Lead(
                first_name="Jane",
                last_name="Smith",
                email="jane.smith@example.com",
                phone="5559876543",
                address="456 Oak Ave",
                city="Chicago",
                state="IL",
                zip_code="60601",
                status=LeadStatus.CONFIRMED,
                area_of_interest="Auto Insurance",
                is_tcpa_compliant=True
            ),
            Lead(
                first_name="Michael",
                last_name="Johnson",
                email="michael.johnson@example.com",
                phone="5552223333",
                address="789 Pine St",
                city="New York",
                state="NY",
                zip_code="10001",
                status=LeadStatus.ASSIGNED,
                area_of_interest="Life Insurance",
                is_tcpa_compliant=True
            ),
            Lead(
                first_name="Emily",
                last_name="Williams",
                email="emily.williams@example.com",
                phone="5554445555",
                address="321 Cedar Rd",
                city="Los Angeles",
                state="CA",
                zip_code="90001",
                status=LeadStatus.CALL_CONNECTED,
                area_of_interest="Home Insurance",
                is_tcpa_compliant=True
            ),
            Lead(
                first_name="David",
                last_name="Brown",
                email="david.brown@example.com",
                phone="5556667777",
                address="654 Birch Ln",
                city="Houston",
                state="TX",
                zip_code="77001",
                status=LeadStatus.CONFIRMED,
                area_of_interest="Health Insurance",
                is_tcpa_compliant=True
            )
        ]
        
        session.add_all(test_leads)
        session.commit()
        
        # Log the created leads
        lead_count = session.query(Lead).count()
        logger.info(f"Created {len(test_leads)} test leads. Total leads: {lead_count}")
        
        # Create some test calls
        test_calls = [
            Call(
                lead_id=test_leads[0].id,
                phone_number=test_leads[0].phone,
                status=CallStatus.SCHEDULED,
                provider="twilio"
            ),
            Call(
                lead_id=test_leads[1].id,
                phone_number=test_leads[1].phone,
                status=CallStatus.CONNECTED,
                provider="deepgram"
            )
        ]
        
        session.add_all(test_calls)
        session.commit()
        
        # Log the created calls
        call_count = session.query(Call).count()
        logger.info(f"Created {len(test_calls)} test calls. Total calls: {call_count}")
        
        logger.info("Database seeded successfully with test data.")
        
    except Exception as e:
        logger.error(f"Error seeding database: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()


def main():
    """Main function to initialize the database."""
    parser = argparse.ArgumentParser(description="Initialize the Voice AI Agent database")
    parser.add_argument("--create", action="store_true", help="Create database tables")
    parser.add_argument("--drop", action="store_true", help="Drop database tables")
    parser.add_argument("--seed", action="store_true", help="Seed database with test data")
    parser.add_argument("--reset", action="store_true", help="Reset database (drop, create, and seed)")
    parser.add_argument("--force", action="store_true", help="Force operations without confirmation")
    
    args = parser.parse_args()
    
    if args.reset:
        if drop_tables(args.force):
            create_tables()
            if args.seed:
                seed_test_data()
    else:
        if args.drop:
            drop_tables(args.force)
        if args.create:
            create_tables()
        if args.seed:
            seed_test_data()
    
    if not any([args.create, args.drop, args.seed, args.reset]):
        parser.print_help()


if __name__ == "__main__":
    main() 