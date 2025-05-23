import os
import sys
import unittest
from pathlib import Path
from datetime import datetime

# Add the parent directory to the path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.database.models import Lead, LeadStatus, Base
from app.database.repository import LeadRepository
from app.database.session import get_db_session, engine

import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class TestDatabase(unittest.TestCase):
    """
    Test the database models and repository.
    """

    @classmethod
    def setUpClass(cls):
        """Set up the test database."""
        # Create a temporary in-memory SQLite database for testing
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(cls.engine)
        cls.SessionFactory = sessionmaker(bind=cls.engine)

    def setUp(self):
        """Set up each test."""
        # Create a new session for each test
        self.session = self.SessionFactory()
        
        # Clean up any existing test data
        self.session.query(Lead).filter_by(email="test@example.com").delete()
        self.session.commit()
        
        # Create a test lead
        self.test_lead = Lead(
            firstname="Test",
            lastname="User",
            email="test@example.com",
            phone1="1234567890",
            address="123 Test St",
            city="Test City",
            state="TS",
            zip="12345",
            status=LeadStatus.PENDING
        )
        
        # Add the test lead to the session
        self.session.add(self.test_lead)
        self.session.commit()
        # Refresh to get the assigned ID
        self.session.refresh(self.test_lead)

    def tearDown(self):
        """Clean up after each test."""
        # Delete any test leads
        self.session.query(Lead).filter_by(email="test@example.com").delete()
        self.session.commit()
        
        # Close the session
        self.session.close()

    def test_lead_creation(self):
        """Test that a lead can be created."""
        # Query the lead from the database
        lead = self.session.query(Lead).filter_by(email="test@example.com").first()
        
        # Check that the lead exists and has the correct data
        self.assertIsNotNone(lead)
        self.assertEqual(lead.firstname, "Test")
        self.assertEqual(lead.lastname, "User")
        self.assertEqual(lead.status, LeadStatus.PENDING)

    def test_lead_status_enum(self):
        """Test the LeadStatus enum."""
        # Check that all required statuses exist
        self.assertEqual(LeadStatus.PENDING.value, "pending")
        self.assertEqual(LeadStatus.CALLING.value, "calling")
        self.assertEqual(LeadStatus.CONFIRMED.value, "confirmed")
        self.assertEqual(LeadStatus.NOT_INTERESTED.value, "not_interested")
        self.assertEqual(LeadStatus.CALL_FAILED.value, "call_failed")
        self.assertEqual(LeadStatus.ENTRY_IN_PROGRESS.value, "entry_in_progress")
        self.assertEqual(LeadStatus.ENTERED.value, "entered")
        self.assertEqual(LeadStatus.ENTRY_FAILED.value, "entry_failed")

    def test_update_lead_status(self):
        """Test updating a lead's status."""
        # Store the ID for later comparison
        test_lead_id = self.test_lead.id
        
        # Update the lead's status
        self.test_lead.status = LeadStatus.CALLING
        self.session.commit()
        
        # Force a flush and refresh to ensure the change is persisted
        self.session.flush()
        self.session.refresh(self.test_lead)
        
        # Query the lead from the database by ID to ensure we get the right one
        lead = self.session.query(Lead).filter_by(id=test_lead_id).first()
        
        # Ensure we found a lead
        self.assertIsNotNone(lead, "Failed to retrieve the lead by ID")
        
        # Ensure we're comparing the same objects by checking IDs
        self.assertEqual(lead.id, self.test_lead.id)
        
        # Check that the status was updated - both on test_lead and queried lead
        self.assertEqual(self.test_lead.status, LeadStatus.CALLING)
        self.assertEqual(lead.status, LeadStatus.CALLING)


class TestRepositoryIntegration(unittest.TestCase):
    """
    Integration tests for the LeadRepository.
    
    Note: These tests require a real database connection and will create and modify data.
    They should be run in a controlled environment, not in production.
    """
    
    def setUp(self):
        """Set up the test database."""
        # Initialize the database
        Base.metadata.create_all(engine)
        
        # Create test lead
        self.test_lead_data = {
            "firstname": "Integration",
            "lastname": "Test",
            "email": "integration@test.com",
            "phone1": "9876543210",
            "address": "456 Integration St",
            "city": "Test City",
            "state": "TS",
            "zip": "54321",
            "status": LeadStatus.PENDING
        }

    def tearDown(self):
        """Clean up the test database."""
        # This is a potentially dangerous operation that should only be done in testing
        # Base.metadata.drop_all(engine)
        pass

    def test_create_lead(self):
        """Test creating a lead through the repository."""
        # Get environment variable and strip any whitespace
        environment = os.getenv("ENVIRONMENT", "").strip()
        print(f"\nENVIRONMENT='{environment}', type={type(environment)}")
        print(f"ENVIRONMENT in ['test', 'development']: {environment in ['test', 'development']}")
        
        # Skip this test if we're not in a test environment
        if environment not in ["test", "development"]:
            print("Skipping test due to ENVIRONMENT not being 'test' or 'development'")
            self.skipTest("Skipping integration test in non-test environment")
        
        print("Running integration test create_lead...")
        
        # Create the lead
        lead_id = LeadRepository.create_lead(self.test_lead_data)
        
        # Check that a lead ID was returned
        self.assertIsNotNone(lead_id)
        
        # Retrieve the lead
        lead = LeadRepository.get_lead_by_id(lead_id)
        
        # Check that the lead has the correct data - lead should be a detached copy with all fields loaded
        self.assertIsNotNone(lead, "Lead not found after creation")
        self.assertEqual(lead.firstname, "Integration")
        self.assertEqual(lead.lastname, "Test")
        self.assertEqual(lead.email, "integration@test.com")
        
        # Clean up - make sure we use a session
        with get_db_session() as session:
            # Find the lead again within this session
            db_lead = session.query(Lead).filter(Lead.id == lead_id).first()
            if db_lead:
                session.delete(db_lead)
                session.commit()


if __name__ == "__main__":
    unittest.main() 