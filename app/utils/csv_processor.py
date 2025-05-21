import os
import csv
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from loguru import logger
from pathlib import Path

from app.database.models import Lead, LeadStatus
from app.database.repository import LeadRepository

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# CSV import/export directories
CSV_IMPORT_DIR = os.getenv("CSV_IMPORT_DIRECTORY", "data/import")
CSV_EXPORT_DIR = os.getenv("CSV_EXPORT_DIRECTORY", "data/export")

# Ensure directories exist
os.makedirs(CSV_IMPORT_DIR, exist_ok=True)
os.makedirs(CSV_EXPORT_DIR, exist_ok=True)


class CSVProcessor:
    """
    Utility class for handling CSV import and export operations.
    """

    # CSV column mappings to Lead model fields
    CSV_TO_MODEL_MAPPING = {
        "Firstname": "firstname",
        "Lastname": "lastname",
        "Email": "email",
        "Phone1": "phone1",
        "Address": "address",
        "Address2": "address2",
        "City": "city",
        "State": "state",
        "Zip": "zip",
        "Gender": "gender",
        "Dob": "dob",
        "Ip": "ip",
        "Subid 2": "subid_2",
        "Signup Url": "signup_url",
        "Consent Url": "consent_url",
        "Education Level": "education_level",
        "Grad Year": "grad_year",
        "Start Date": "start_date",
        "Military Type": "military_type",
        "Campus Type": "campus_type",
        "Area Of Study": "area_of_study",
        "Level Of Interest": "level_of_interest",
        "Computer with Internet": "computer_with_internet",
        "US Citizen": "us_citizen",
        "Registered Nurse": "registered_nurse",
        "Teaching License": "teaching_license",
        "Enroll Status": "enroll_status"
    }

    # Model fields to CSV column mappings for export
    MODEL_TO_CSV_MAPPING = {v: k for k, v in CSV_TO_MODEL_MAPPING.items()}

    # Additional fields to include in export
    EXPORT_ADDITIONAL_FIELDS = {
        "status": "Status",
        "tcpa_accepted": "TCPA Accepted",
        "confirmed_area_of_interest": "Confirmed Area of Interest",
        "call_recording_url": "Call Recording URL",
        "call_notes": "Call Notes",
        "entry_notes": "Entry Notes"
    }

    @classmethod
    def import_csv_file(cls, file_path: str) -> Tuple[int, int, List[str]]:
        """
        Import leads from a CSV file.

        Parameters:
        -----------
        file_path : str
            Path to the CSV file to import.

        Returns:
        --------
        Tuple[int, int, List[str]]
            A tuple containing (success_count, failure_count, error_messages).
        """
        if not os.path.exists(file_path):
            logger.error(f"CSV file not found: {file_path}")
            return 0, 1, ["File not found"]

        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            
            # Check required columns
            required_columns = ["Firstname", "Lastname", "Email", "Phone1"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                error_msg = f"CSV file missing required columns: {', '.join(missing_columns)}"
                logger.error(error_msg)
                return 0, df.shape[0], [error_msg]
            
            # Convert DataFrame to list of dictionaries
            leads_data = []
            error_rows = []
            
            for index, row in df.iterrows():
                try:
                    lead_data = {}
                    
                    # Map CSV columns to model fields
                    for csv_col, model_field in cls.CSV_TO_MODEL_MAPPING.items():
                        if csv_col in df.columns:
                            # Handle empty or NaN values
                            value = row[csv_col]
                            if pd.notna(value):
                                lead_data[model_field] = str(value).strip()
                            else:
                                lead_data[model_field] = None
                    
                    # Set default status
                    lead_data["status"] = LeadStatus.PENDING
                    
                    # Add to leads data
                    leads_data.append(lead_data)
                except Exception as e:
                    logger.error(f"Error processing row {index}: {str(e)}")
                    error_rows.append(index)
            
            # Bulk insert leads
            success_count, failure_count = LeadRepository.bulk_create_leads(leads_data)
            
            # Move the processed file to a processed directory
            processed_dir = os.path.join(os.path.dirname(file_path), "processed")
            os.makedirs(processed_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            processed_file = os.path.join(
                processed_dir, 
                f"{Path(file_path).stem}_{timestamp}{Path(file_path).suffix}"
            )
            
            os.rename(file_path, processed_file)
            
            logger.info(f"CSV import completed. Success: {success_count}, Failures: {failure_count}")
            return success_count, failure_count, [f"Error in row {idx}" for idx in error_rows]
            
        except Exception as e:
            logger.error(f"Error importing CSV: {str(e)}")
            return 0, 1, [str(e)]

    @classmethod
    def export_leads_to_csv(cls, leads: List[Lead], file_path: Optional[str] = None) -> str:
        """
        Export leads to a CSV file.

        Parameters:
        -----------
        leads : List[Lead]
            List of leads to export.
        file_path : Optional[str], default=None
            Path to the output CSV file. If None, a default path will be generated.

        Returns:
        --------
        str
            Path to the exported CSV file.
        """
        try:
            if not file_path:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                file_path = os.path.join(CSV_EXPORT_DIR, f"exported_leads_{timestamp}.csv")
            
            # Prepare data for export                                       
            export_data = []
            
            for lead in leads:
                lead_data = {}
                
                # Add basic fields
                for model_field, csv_col in cls.MODEL_TO_CSV_MAPPING.items():
                    if hasattr(lead, model_field):
                        lead_data[csv_col] = getattr(lead, model_field)
                
                # Add additional fields
                for model_field, csv_col in cls.EXPORT_ADDITIONAL_FIELDS.items():
                    if hasattr(lead, model_field):
                        value = getattr(lead, model_field)
                        
                        # Handle special cases
                        if model_field == "status" and value is not None:
                            lead_data[csv_col] = value.value
                        elif model_field == "tcpa_accepted":
                            lead_data[csv_col] = "Yes" if value else "No"
                        else:
                            lead_data[csv_col] = value
                
                export_data.append(lead_data)
            
            # Create DataFrame and export to CSV
            df = pd.DataFrame(export_data)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            df.to_csv(file_path, index=False)
            
            logger.info(f"Exported {len(leads)} leads to {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error exporting leads to CSV: {str(e)}")
            raise

    @classmethod
    def process_new_csv_files(cls) -> Dict[str, Any]:
        """
        Process all new CSV files in the import directory.

        Returns:
        --------
        Dict[str, Any]
            A dictionary with import statistics.
        """
        results = {
            "total_files": 0,
            "processed_files": 0,
            "failed_files": 0,
            "total_leads": 0,
            "imported_leads": 0,
            "failed_leads": 0,
            "files": []
        }
        
        try:
            # Get all CSV files in the import directory
            csv_files = [
                os.path.join(CSV_IMPORT_DIR, f) 
                for f in os.listdir(CSV_IMPORT_DIR) 
                if f.lower().endswith(".csv") and os.path.isfile(os.path.join(CSV_IMPORT_DIR, f))
            ]
            
            results["total_files"] = len(csv_files)
            
            # Process each file
            for file_path in csv_files:
                file_result = {
                    "file": os.path.basename(file_path),
                    "status": "success",
                    "imported": 0,
                    "failed": 0,
                    "error": None
                }
                
                try:
                    success, failure, errors = cls.import_csv_file(file_path)
                    
                    file_result["imported"] = success
                    file_result["failed"] = failure
                    results["imported_leads"] += success
                    results["failed_leads"] += failure
                    results["total_leads"] += (success + failure)
                    
                    if failure > 0:
                        file_result["error"] = errors[0] if errors else "Unknown error"
                        file_result["status"] = "partial"
                    
                    results["processed_files"] += 1
                    
                except Exception as e:
                    file_result["status"] = "failed"
                    file_result["error"] = str(e)
                    results["failed_files"] += 1
                
                results["files"].append(file_result)
            
            logger.info(f"CSV processing completed. Files: {results['processed_files']}/{results['total_files']}, Leads: {results['imported_leads']}/{results['total_leads']}")
            return results
            
        except Exception as e:
            logger.error(f"Error processing CSV files: {str(e)}")
            return results 