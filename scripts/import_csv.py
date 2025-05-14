"""
Script to import leads from a CSV file into the database.
This is used to load initial lead data exported from Go High Level (GHL).
"""

import os
import sys
import argparse
import csv
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

# Add the parent directory to the module search path
sys.path.append(str(Path(__file__).parent.parent))

from database.models import get_session, Lead, LeadStatus
from shared import utils
from shared.logging_setup import setup_logging, setup_stdlib_logging

# Set up logging
logger = setup_logging("import_csv")
setup_stdlib_logging()

def map_csv_to_lead(row: Dict[str, str], mapping: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Map a row from the CSV file to a lead object.
    
    Args:
        row: A dictionary representing a row from the CSV file
        mapping: Optional mapping of CSV column names to lead field names
    
    Returns:
        A dictionary with lead data ready to be inserted into the database
    """
    # Default mapping (CSV column name -> Lead field name)
    default_mapping = {
        'Name': 'name',
        'Email': 'email',
        'Phone': 'phone',
        'Address': 'address',
        'Street': 'street',
        'City': 'city',
        'State': 'state',
        'Zip': 'zip_code',
        'ZIP': 'zip_code',
        'ZipCode': 'zip_code',
        'Zip Code': 'zip_code',
        'Area of Interest': 'area_of_interest',
        'Interest': 'area_of_interest',
        'TCPA Consent': 'tcpa_consent',
        'Consent': 'tcpa_consent',
        'OptIn': 'tcpa_consent',
        'Opt-In': 'tcpa_consent',
        'Source': 'source'
    }
    
    # Use provided mapping if available, otherwise use default
    field_mapping = mapping or default_mapping
    
    # Initialize lead data with default values
    lead_data = {
        'status': LeadStatus.PENDING,
        'source': 'CSV Import',
        'original_data': row  # Store the original CSV data
    }
    
    # Map fields from CSV to lead data using the mapping
    for csv_column, lead_field in field_mapping.items():
        if csv_column in row:
            value = row[csv_column].strip()
            
            if lead_field == 'tcpa_consent':
                # Convert text values to boolean
                lead_data[lead_field] = value.lower() in ('yes', 'true', '1', 'y', 'opt-in', 'optin')
            elif lead_field == 'phone':
                # Format phone number
                lead_data[lead_field] = utils.format_phone_number(value) if value else None
            else:
                lead_data[lead_field] = value if value else None
    
    # Ensure required fields are present
    if 'name' not in lead_data or not lead_data['name']:
        # If no name, try to generate one from other fields
        if row.get('First Name') and row.get('Last Name'):
            lead_data['name'] = f"{row['First Name']} {row['Last Name']}".strip()
        else:
            # Use email or phone as a fallback
            lead_data['name'] = lead_data.get('email') or lead_data.get('phone') or "Unknown"
    
    # If we have a full address but not individual components, parse them
    if lead_data.get('address') and not all([lead_data.get('street'), lead_data.get('city'), lead_data.get('state'), lead_data.get('zip_code')]):
        address_parts = utils.parse_address(lead_data['address'])
        for key, value in address_parts.items():
            if key in ['street', 'city', 'state', 'zip'] and value:
                lead_data[key if key != 'zip' else 'zip_code'] = value
    
    return lead_data

def import_csv_to_db(csv_file: str, mapping_file: Optional[str] = None, 
                   dedup: bool = True, dry_run: bool = False,
                   batch_size: int = 100) -> int:
    """
    Import leads from a CSV file into the database.
    
    Args:
        csv_file: Path to the CSV file to import
        mapping_file: Optional path to a JSON file containing column mapping
        dedup: Whether to check for duplicates
        dry_run: If True, don't actually insert into the database
        batch_size: Number of records to insert in each batch
    
    Returns:
        Number of leads imported
    """
    if not os.path.exists(csv_file):
        logger.error(f"CSV file not found: {csv_file}")
        return 0
    
    # Load custom mapping if provided
    mapping = None
    if mapping_file:
        if os.path.exists(mapping_file):
            try:
                with open(mapping_file, 'r') as f:
                    mapping = json.load(f)
                logger.info(f"Loaded custom mapping from {mapping_file}")
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in mapping file: {mapping_file}")
                return 0
        else:
            logger.error(f"Mapping file not found: {mapping_file}")
            return 0
    
    # Open the CSV file
    try:
        with open(csv_file, 'r', newline='', encoding='utf-8') as f:
            # Get the CSV dialect
            dialect = csv.Sniffer().sniff(f.read(1024))
            f.seek(0)
            
            # Read the header to get field names
            reader = csv.reader(f, dialect)
            header = next(reader)
            
            # Check if the CSV has any rows
            if not header:
                logger.error("CSV file is empty or has no header row")
                return 0
            
            # Create a DictReader with the header
            f.seek(0)
            csv_reader = csv.DictReader(f, dialect=dialect)
            
            # Import the leads
            leads = []
            imported_count = 0
            
            session = get_session() if not dry_run else None
            
            try:
                # Keep track of seen emails and phones for deduplication
                seen_emails = set()
                seen_phones = set()
                
                # Process each row in the CSV
                for i, row in enumerate(csv_reader):
                    try:
                        # Map CSV row to lead data
                        lead_data = map_csv_to_lead(row, mapping)
                        
                        # Skip leads without either an email or phone
                        if not lead_data.get('email') and not lead_data.get('phone'):
                            logger.warning(f"Skipping row {i+1}: No email or phone")
                            continue
                        
                        # Check for duplicates if dedup is enabled
                        if dedup:
                            email = lead_data.get('email')
                            phone = lead_data.get('phone')
                            
                            # Skip if we've already seen this email or phone
                            if email and email in seen_emails:
                                logger.warning(f"Skipping duplicate email: {email}")
                                continue
                            if phone and phone in seen_phones:
                                logger.warning(f"Skipping duplicate phone: {phone}")
                                continue
                            
                            # Add to seen sets
                            if email:
                                seen_emails.add(email)
                            if phone:
                                seen_phones.add(phone)
                        
                        # For dry run, just print the lead data
                        if dry_run:
                            logger.info(f"Would import lead: {lead_data}")
                            imported_count += 1
                            continue
                        
                        # Create the lead object
                        lead = Lead(**lead_data)
                        leads.append(lead)
                        
                        # Insert in batches
                        if len(leads) >= batch_size:
                            session.add_all(leads)
                            session.commit()
                            imported_count += len(leads)
                            logger.info(f"Imported {imported_count} leads so far...")
                            leads = []
                    
                    except Exception as e:
                        logger.error(f"Error processing row {i+1}: {str(e)}")
                        if not dry_run:
                            session.rollback()
                
                # Insert any remaining leads
                if leads and not dry_run:
                    session.add_all(leads)
                    session.commit()
                    imported_count += len(leads)
                
                logger.info(f"Successfully imported {imported_count} leads")
                return imported_count
            
            finally:
                if session:
                    session.close()
    
    except Exception as e:
        logger.error(f"Error importing CSV file: {str(e)}")
        return 0

def main():
    """Main function for importing CSV data"""
    parser = argparse.ArgumentParser(description="Import leads from a CSV file")
    parser.add_argument('csv_file', help='Path to the CSV file to import')
    parser.add_argument('--mapping', help='Path to a JSON file with column mapping')
    parser.add_argument('--no-dedup', action='store_true', 
                        help='Disable deduplication by email and phone')
    parser.add_argument('--dry-run', action='store_true',
                        help='Do not actually insert into the database')
    parser.add_argument('--batch-size', type=int, default=100,
                        help='Number of records to insert in each batch')
    
    args = parser.parse_args()
    
    import_csv_to_db(
        args.csv_file, 
        args.mapping, 
        not args.no_dedup, 
        args.dry_run, 
        args.batch_size
    )

if __name__ == "__main__":
    main() 