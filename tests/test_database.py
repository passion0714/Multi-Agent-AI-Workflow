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

    def tearDown(self):
        """Clean up after each test."""
        # Roll back the transaction to clean up
        self.session.rollback()
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
        # Update the lead's status
        self.test_lead.status = LeadStatus.CALLING
        self.session.commit()
        
        # Query the lead from the database
        lead = self.session.query(Lead).filter_by(email="test@example.com").first()
        
        # Check that the status was updated
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
        # Skip this test if we're not in a test environment
        if os.getenv("ENVIRONMENT") not in ["test", "development"]:
            self.skipTest("Skipping integration test in non-test environment")
            
        # Create the lead
        lead_id = LeadRepository.create_lead(self.test_lead_data)
        
        # Check that a lead ID was returned
        self.assertIsNotNone(lead_id)
        
        # Retrieve the lead
        lead = LeadRepository.get_lead_by_id(lead_id)
        
        # Check that the lead has the correct data
        self.assertEqual(lead.firstname, "Integration")
        self.assertEqual(lead.lastname, "Test")
        self.assertEqual(lead.email, "integration@test.com")
        
        # Clean up
        with get_db_session() as session:
            session.delete(lead)
            session.commit()


if __name__ == "__main__":
    unittest.main() 