import os
import sys
import unittest
import tempfile
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add the parent directory to the path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.utils.csv_processor import CSVProcessor
from app.database.models import Lead, LeadStatus, Base
from app.database.repository import LeadRepository
from app.database.session import engine


class TestCSVProcessor(unittest.TestCase):
    """
    Test the CSV processor functionality.
    """
    
    def setUp(self):
        """Set up the test."""
        # Initialize the database
        Base.metadata.create_all(engine)
        
        # Create a temporary directory for test CSV files
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create a sample CSV file
        self.sample_data = {
            "Firstname": ["John", "Jane"],
            "Lastname": ["Doe", "Smith"],
            "Email": ["john.doe@example.com", "jane.smith@example.com"],
            "Phone1": ["1234567890", "0987654321"],
            "Address": ["123 Main St", "456 Elm St"],
            "Address2": ["Apt 1", "Suite 2"],
            "City": ["New York", "Los Angeles"],
            "State": ["NY", "CA"],
            "Zip": ["10001", "90001"],
            "Gender": ["M", "F"],
            "Education Level": ["Bachelors Degree", "Masters Degree"],
            "Area Of Study": ["Computer Science", "Business"],
            "Level Of Interest": ["8", "9"]
        }
        
        self.sample_csv_path = os.path.join(self.temp_dir.name, "sample_leads.csv")
        pd.DataFrame(self.sample_data).to_csv(self.sample_csv_path, index=False)
    
    def tearDown(self):
        """Clean up after the test."""
        # Remove the temporary directory
        self.temp_dir.cleanup()
        
        # Clean up any test leads
        from app.database.session import get_db_session
        with get_db_session() as session:
            session.query(Lead).filter(
                Lead.email.in_(["john.doe@example.com", "jane.smith@example.com"])
            ).delete(synchronize_session=False)
            session.commit()
    
    def test_import_csv_file(self):
        """Test importing a CSV file."""
        # Skip this test if we're not in a test environment
        if os.getenv("ENVIRONMENT") not in ["test", "development"]:
            self.skipTest("Skipping integration test in non-test environment")
        
        # Import the CSV file
        success_count, failure_count, errors = CSVProcessor.import_csv_file(self.sample_csv_path)
        
        # Check the results
        self.assertEqual(success_count, 2, f"Expected 2 successes, got {success_count}")
        self.assertEqual(failure_count, 0, f"Expected 0 failures, got {failure_count}")
        self.assertEqual(len(errors), 0, f"Expected 0 errors, got {len(errors)}")
        
        # Check that the leads were created in the database
        from app.database.session import get_db_session
        with get_db_session() as session:
            john = session.query(Lead).filter_by(email="john.doe@example.com").first()
            jane = session.query(Lead).filter_by(email="jane.smith@example.com").first()
            
            self.assertIsNotNone(john, "John Doe lead not found in database")
            self.assertIsNotNone(jane, "Jane Smith lead not found in database")
            
            self.assertEqual(john.firstname, "John")
            self.assertEqual(john.lastname, "Doe")
            self.assertEqual(john.phone1, "1234567890")
            self.assertEqual(john.city, "New York")
            
            self.assertEqual(jane.firstname, "Jane")
            self.assertEqual(jane.lastname, "Smith")
            self.assertEqual(jane.phone1, "0987654321")
            self.assertEqual(jane.city, "Los Angeles")
    
    def test_export_leads_to_csv(self):
        """Test exporting leads to a CSV file."""
        # Skip this test if we're not in a test environment
        if os.getenv("ENVIRONMENT") not in ["test", "development"]:
            self.skipTest("Skipping integration test in non-test environment")
        
        # Create some test leads in the database
        lead1 = Lead(
            firstname="Export",
            lastname="Test1",
            email="export.test1@example.com",
            phone1="1112223333",
            address="789 Oak St",
            city="Chicago",
            state="IL",
            zip="60601",
            status=LeadStatus.PENDING
        )
        
        lead2 = Lead(
            firstname="Export",
            lastname="Test2",
            email="export.test2@example.com",
            phone1="4445556666",
            address="321 Pine St",
            city="Seattle",
            state="WA",
            zip="98101",
            status=LeadStatus.CONFIRMED,
            confirmed_email="confirmed@example.com",
            confirmed_area_of_interest="Data Science",
            tcpa_accepted=True
        )
        
        # Add the leads to the database
        from app.database.session import get_db_session
        with get_db_session() as session:
            session.add(lead1)
            session.add(lead2)
            session.commit()
            # Refresh the leads to get their IDs
            session.refresh(lead1)
            session.refresh(lead2)
        
        try:
            # Export the leads to a CSV file
            export_path = os.path.join(self.temp_dir.name, "exported_leads.csv")
            result_path = CSVProcessor.export_leads_to_csv([lead1, lead2], export_path)
            
            # Check that the export was successful
            self.assertEqual(result_path, export_path)
            self.assertTrue(os.path.exists(export_path))
            
            # Read the exported CSV file
            exported_df = pd.read_csv(export_path)
            
            # Check that the exported data is correct
            self.assertEqual(len(exported_df), 2)
            self.assertTrue("Firstname" in exported_df.columns)
            self.assertTrue("Email" in exported_df.columns)
            self.assertTrue("Status" in exported_df.columns)
            
            # Check specific values
            self.assertEqual(exported_df.iloc[0]["Firstname"], "Export")
            self.assertEqual(exported_df.iloc[0]["Lastname"], "Test1")
            self.assertEqual(exported_df.iloc[0]["Status"], "pending")
            
            self.assertEqual(exported_df.iloc[1]["Firstname"], "Export")
            self.assertEqual(exported_df.iloc[1]["Lastname"], "Test2")
            self.assertEqual(exported_df.iloc[1]["Status"], "confirmed")
            self.assertEqual(exported_df.iloc[1]["Confirmed Area of Interest"], "Data Science")
            self.assertEqual(exported_df.iloc[1]["TCPA Accepted"], "Yes")
            
        finally:
            # Clean up the test leads
            with get_db_session() as session:
                session.query(Lead).filter(
                    Lead.email.in_(["export.test1@example.com", "export.test2@example.com"])
                ).delete(synchronize_session=False)
                session.commit()


if __name__ == "__main__":
    unittest.main() 