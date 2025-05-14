"""
Lead Hoop Mapper module for mapping lead data to form fields.

This module contains functions to map lead data from our database schema
to the appropriate form field selectors and values for the Lead Hoop portal.
"""

import sys
from typing import Dict, Any, List, Optional
from pathlib import Path

# Add the parent directory to the module search path
sys.path.append(str(Path(__file__).parent.parent))

from database.models import Lead, LeadStatus
from shared import config, utils

# Define common form field selectors for Lead Hoop
# These would be determined by inspecting the actual Lead Hoop form
# For now, we're using generic selectors that are likely to match
FIELD_SELECTORS = {
    # Basic contact information
    "name": "input[name='name'], input[name='lead_name'], input[name='customer_name']",
    "email": "input[name='email'], input[type='email']",
    "phone": "input[name='phone'], input[name='phone_number'], input[type='tel']",
    
    # Address fields
    "address": "input[name='address'], textarea[name='address']",
    "street": "input[name='street'], input[name='address_line1']",
    "city": "input[name='city']",
    "state": "select[name='state'], input[name='state']",
    "zip_code": "input[name='zip'], input[name='zip_code'], input[name='postal_code']",
    
    # Additional information
    "area_of_interest": "select[name='interest'], select[name='area_of_interest'], select[name='product']",
    "tcpa_consent": "input[name='consent'], input[name='tcpa_consent'], input[type='checkbox'][name='consent']",
    
    # Source information
    "source": "select[name='source'], input[name='source']",
    "notes": "textarea[name='notes'], textarea[name='comments']",
}

# Define mappings for dropdown values
INTEREST_MAPPINGS = {
    "Home Insurance": "home",
    "Auto Insurance": "auto",
    "Life Insurance": "life",
    "Health Insurance": "health",
    "Business Insurance": "business",
    "Other": "other"
}

STATE_MAPPINGS = {
    "AL": "AL", "AK": "AK", "AZ": "AZ", "AR": "AR", "CA": "CA", "CO": "CO", "CT": "CT",
    "DE": "DE", "FL": "FL", "GA": "GA", "HI": "HI", "ID": "ID", "IL": "IL", "IN": "IN",
    "IA": "IA", "KS": "KS", "KY": "KY", "LA": "LA", "ME": "ME", "MD": "MD", "MA": "MA",
    "MI": "MI", "MN": "MN", "MS": "MS", "MO": "MO", "MT": "MT", "NE": "NE", "NV": "NV",
    "NH": "NH", "NJ": "NJ", "NM": "NM", "NY": "NY", "NC": "NC", "ND": "ND", "OH": "OH",
    "OK": "OK", "OR": "OR", "PA": "PA", "RI": "RI", "SC": "SC", "SD": "SD", "TN": "TN",
    "TX": "TX", "UT": "UT", "VT": "VT", "VA": "VA", "WA": "WA", "WV": "WV", "WI": "WI",
    "WY": "WY", "DC": "DC"
}

def map_lead_to_form_fields(lead: Lead) -> Dict[str, Any]:
    """
    Map lead data to form field selectors and values for Lead Hoop.
    
    Args:
        lead: The lead to map
        
    Returns:
        Dictionary mapping form field selectors to values
    """
    field_mapping = {}
    
    # Map basic contact information
    if lead.name:
        field_mapping[FIELD_SELECTORS["name"]] = lead.name
    
    if lead.email:
        field_mapping[FIELD_SELECTORS["email"]] = lead.email
    
    if lead.phone:
        # Format phone number appropriately for the form
        # Some forms expect (123) 456-7890, others just digits
        # Here we're providing the full E.164 format
        field_mapping[FIELD_SELECTORS["phone"]] = lead.phone
    
    # Map address information
    if lead.address:
        field_mapping[FIELD_SELECTORS["address"]] = lead.address
    
    if lead.street:
        field_mapping[FIELD_SELECTORS["street"]] = lead.street
    
    if lead.city:
        field_mapping[FIELD_SELECTORS["city"]] = lead.city
    
    if lead.state:
        # For state, we might need to use a dropdown value
        if _is_dropdown_field(FIELD_SELECTORS["state"]):
            field_mapping[FIELD_SELECTORS["state"]] = {
                "type": "select",
                "value": STATE_MAPPINGS.get(lead.state.upper(), lead.state)
            }
        else:
            field_mapping[FIELD_SELECTORS["state"]] = lead.state
    
    if lead.zip_code:
        field_mapping[FIELD_SELECTORS["zip_code"]] = lead.zip_code
    
    # Map area of interest
    if lead.area_of_interest:
        # For area of interest, we likely need to use a dropdown value
        if _is_dropdown_field(FIELD_SELECTORS["area_of_interest"]):
            interest_value = INTEREST_MAPPINGS.get(lead.area_of_interest, "other")
            field_mapping[FIELD_SELECTORS["area_of_interest"]] = {
                "type": "select",
                "value": interest_value
            }
        else:
            field_mapping[FIELD_SELECTORS["area_of_interest"]] = lead.area_of_interest
    
    # Map TCPA consent
    if FIELD_SELECTORS["tcpa_consent"]:
        field_mapping[FIELD_SELECTORS["tcpa_consent"]] = lead.tcpa_consent
    
    # Map source
    if lead.source:
        field_mapping[FIELD_SELECTORS["source"]] = lead.source
    
    # Add notes about the lead
    notes = []
    if lead.call_notes:
        notes.append(f"Call Notes: {lead.call_notes}")
    
    if lead.voice_consent_recording_url:
        notes.append(f"Voice Consent Recording: {lead.voice_consent_recording_url}")
    
    if notes:
        field_mapping[FIELD_SELECTORS["notes"]] = "\n".join(notes)
    
    return field_mapping

def map_error_to_fields(error_message: str) -> List[str]:
    """
    Map error messages to potential field selectors.
    
    This helps identify which fields might be causing validation errors.
    
    Args:
        error_message: The error message from the form
        
    Returns:
        List of field selectors that might be causing the error
    """
    error_message = error_message.lower()
    potential_fields = []
    
    # Map common error phrases to fields
    if any(term in error_message for term in ["name", "full name"]):
        potential_fields.append(FIELD_SELECTORS["name"])
    
    if any(term in error_message for term in ["email", "e-mail", "email address"]):
        potential_fields.append(FIELD_SELECTORS["email"])
    
    if any(term in error_message for term in ["phone", "telephone", "phone number"]):
        potential_fields.append(FIELD_SELECTORS["phone"])
    
    if any(term in error_message for term in ["address", "street"]):
        potential_fields.append(FIELD_SELECTORS["address"])
        potential_fields.append(FIELD_SELECTORS["street"])
    
    if "city" in error_message:
        potential_fields.append(FIELD_SELECTORS["city"])
    
    if any(term in error_message for term in ["state", "province"]):
        potential_fields.append(FIELD_SELECTORS["state"])
    
    if any(term in error_message for term in ["zip", "postal", "zip code"]):
        potential_fields.append(FIELD_SELECTORS["zip_code"])
    
    if any(term in error_message for term in ["interest", "product", "service"]):
        potential_fields.append(FIELD_SELECTORS["area_of_interest"])
    
    if any(term in error_message for term in ["consent", "agree", "permission", "tcpa"]):
        potential_fields.append(FIELD_SELECTORS["tcpa_consent"])
    
    return potential_fields

def get_dynamic_field_mapping(field_name: str, field_value: str) -> Dict[str, str]:
    """
    Generate a mapping for a field not covered by the default mappings.
    
    This is useful when the Lead Hoop form has custom fields that aren't
    part of our standard mapping.
    
    Args:
        field_name: The name of the custom field
        field_value: The value for the custom field
        
    Returns:
        Dictionary mapping the custom field selector to its value
    """
    # Generate a selector based on the field name
    selector = f"input[name='{field_name}'], textarea[name='{field_name}'], select[name='{field_name}']"
    
    return {selector: field_value}

def _is_dropdown_field(selector: str) -> bool:
    """
    Check if a field selector is likely to be a dropdown (select) field.
    
    Args:
        selector: The field selector to check
        
    Returns:
        True if the selector is likely a dropdown field, False otherwise
    """
    return "select" in selector.lower()

def _is_checkbox_field(selector: str) -> bool:
    """
    Check if a field selector is likely to be a checkbox field.
    
    Args:
        selector: The field selector to check
        
    Returns:
        True if the selector is likely a checkbox field, False otherwise
    """
    return "checkbox" in selector.lower() or "consent" in selector.lower()

def _is_radio_field(selector: str) -> bool:
    """
    Check if a field selector is likely to be a radio field.
    
    Args:
        selector: The field selector to check
        
    Returns:
        True if the selector is likely a radio field, False otherwise
    """
    return "radio" in selector.lower()

def update_field_selectors(new_selectors: Dict[str, str]):
    """
    Update the field selectors based on observations of the Lead Hoop form.
    
    This would be used if we discover that our selectors aren't matching
    the actual form elements in Lead Hoop.
    
    Args:
        new_selectors: Dictionary of field names to new selectors
    """
    global FIELD_SELECTORS
    
    for field, selector in new_selectors.items():
        if field in FIELD_SELECTORS:
            FIELD_SELECTORS[field] = selector 