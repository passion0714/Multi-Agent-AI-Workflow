"""
Conversation script module for the Voice Agent.

This module generates conversation scripts for the Voice API,
customized for each lead based on their existing information.
"""

import sys
from typing import Dict, Any, List, Optional
from pathlib import Path

# Add the parent directory to the module search path
sys.path.append(str(Path(__file__).parent.parent))

from database.models import Lead
from shared import utils

def get_conversation_script(lead: Lead) -> Dict[str, Any]:
    """
    Generate a conversation script for a lead.
    
    This function creates a script that guides the conversation flow
    for the Voice API, customized based on the lead's existing information.
    
    Args:
        lead: The lead to generate a script for
        
    Returns:
        A conversation script in the format expected by the Voice API
    """
    # Get lead attributes with fallbacks to empty strings
    name = lead.name or "there"
    email = lead.email or ""
    phone = lead.phone or ""
    address = lead.address or ""
    area_of_interest = lead.area_of_interest or ""
    
    # Basic greeting and introduction
    greeting = f"Hello, I'm calling for {name}. This is an automated call from MERGE AI. Am I speaking with {name}?"
    
    # Introduction to the purpose of the call
    introduction = "I'm calling to confirm some information about your recent inquiry about insurance options. This call may be recorded for quality assurance purposes."
    
    # The main script will vary based on what information we already have
    # and what the Voice API platform expects
    
    # For this example, we'll use a simplified format that works with our simulated Voice API
    # In a real implementation, this would be formatted according to the specific Voice API requirements
    
    # For VAPI, a script might look like a JSON structure with conversation nodes
    # For Synthflow, it might be a YAML-like format
    # For Assistable, it could be a directed conversation flow
    
    script = {
        "name": "lead_confirmation_call",
        "version": "1.0",
        "call_type": "outbound",
        "target_phone": lead.phone,
        "initial_greeting": greeting,
        "introduction": introduction,
        "lead_data": {
            "name": name,
            "email": email,
            "phone": phone,
            "address": address,
            "area_of_interest": area_of_interest
        },
        "conversation_flow": get_conversation_flow(lead),
        "fallback_responses": get_fallback_responses(),
        "exit_messages": get_exit_messages()
    }
    
    return script

def get_conversation_flow(lead: Lead) -> List[Dict[str, Any]]:
    """
    Generate the main conversation flow based on the lead's existing information.
    
    Args:
        lead: The lead to generate the conversation flow for
        
    Returns:
        A list of conversation nodes defining the flow
    """
    flow = []
    
    # Start with confirmation that we're speaking to the right person
    flow.append({
        "id": "confirm_identity",
        "type": "confirmation",
        "message": f"Just to confirm, am I speaking with {lead.name}?",
        "responses": {
            "yes": "Great, thank you for confirming.",
            "no": "I apologize for the confusion. Would it be possible to speak with {lead.name}?"
        },
        "next": {
            "yes": "explain_purpose",
            "no": "wrong_person"
        }
    })
    
    # Handle case where we're not speaking to the right person
    flow.append({
        "id": "wrong_person",
        "type": "confirmation",
        "message": "Would it be possible to speak with {lead.name} now?",
        "responses": {
            "yes": "Great, I'll wait while you get them.",
            "no": "No problem. Could you let them know we called about their insurance inquiry? We'll try again later."
        },
        "next": {
            "yes": "wait_for_person",
            "no": "exit_unavailable"
        }
    })
    
    # Wait for the right person to come to the phone
    flow.append({
        "id": "wait_for_person",
        "type": "message",
        "message": "Thank you, I'll wait.",
        "wait_time": 10,  # seconds
        "next": "confirm_identity_again"
    })
    
    # Confirm identity again after the right person comes to the phone
    flow.append({
        "id": "confirm_identity_again",
        "type": "confirmation",
        "message": f"Hello, is this {lead.name}?",
        "responses": {
            "yes": "Thank you for confirming. I'm calling about your recent insurance inquiry.",
            "no": "I apologize for the confusion. We'll try to reach {lead.name} at a later time."
        },
        "next": {
            "yes": "explain_purpose",
            "no": "exit_unavailable"
        }
    })
    
    # Explain the purpose of the call
    flow.append({
        "id": "explain_purpose",
        "type": "message",
        "message": "I'm calling to confirm some information about your recent inquiry about insurance options. " +
                   "This will take just a couple of minutes and will help us find the best insurance options for you. " +
                   "Is now a good time to talk?",
        "next": "confirm_time"
    })
    
    # Confirm if it's a good time to talk
    flow.append({
        "id": "confirm_time",
        "type": "confirmation",
        "message": "Is now a good time for us to confirm your information?",
        "responses": {
            "yes": "Great, I'll keep this brief.",
            "no": "I understand. When would be a better time for us to call back?"
        },
        "next": {
            "yes": "confirm_interest",
            "no": "schedule_callback"
        }
    })
    
    # Handle scheduling a callback
    flow.append({
        "id": "schedule_callback",
        "type": "open_ended",
        "message": "When would be a better time for us to call you back?",
        "next": "confirm_callback_time"
    })
    
    # Confirm the callback time
    flow.append({
        "id": "confirm_callback_time",
        "type": "confirmation",
        "message": "I'll note that we should call back at {response}. Is that correct?",
        "responses": {
            "yes": "Great, we'll call you back then. Thank you for your time.",
            "no": "I apologize for the misunderstanding. Let's try once more."
        },
        "next": {
            "yes": "exit_callback",
            "no": "schedule_callback"
        }
    })
    
    # Confirm interest in insurance
    flow.append({
        "id": "confirm_interest",
        "type": "confirmation",
        "message": f"Our records show you're interested in insurance options" + 
                   (f" specifically for {lead.area_of_interest}" if lead.area_of_interest else "") + 
                   ". Is that correct?",
        "responses": {
            "yes": "Great! Let's make sure we have your information correct.",
            "no": "I see. What type of insurance are you interested in?"
        },
        "next": {
            "yes": "confirm_contact_info",
            "no": "update_interest"
        }
    })
    
    # Update the area of interest if needed
    flow.append({
        "id": "update_interest",
        "type": "options",
        "message": "What type of insurance are you most interested in?",
        "options": [
            "Auto Insurance",
            "Home Insurance",
            "Life Insurance",
            "Health Insurance",
            "Business Insurance",
            "Other"
        ],
        "next": "confirm_contact_info"
    })
    
    # Confirm contact information
    flow.append({
        "id": "confirm_contact_info",
        "type": "confirmation",
        "message": f"I have your contact information as: " +
                   (f"Email: {lead.email}, " if lead.email else "No email on file, ") +
                   f"Phone: {lead.phone}. Is this information correct?",
        "responses": {
            "yes": "Thank you for confirming.",
            "no": "I apologize for the error. Let's update your information."
        },
        "next": {
            "yes": "confirm_email" if not lead.email else "confirm_address",
            "no": "update_contact_info"
        }
    })
    
    # Update contact information if needed
    flow.append({
        "id": "update_contact_info",
        "type": "confirmation",
        "message": "Would you like to update your email, your phone number, or both?",
        "options": ["Email", "Phone", "Both"],
        "next": {
            "Email": "update_email",
            "Phone": "update_phone",
            "Both": "update_email_then_phone"
        }
    })
    
    # Update email if needed
    flow.append({
        "id": "update_email",
        "type": "open_ended",
        "message": "What is your current email address?",
        "next": "confirm_email_update"
    })
    
    # Confirm email update
    flow.append({
        "id": "confirm_email_update",
        "type": "confirmation",
        "message": "I have your email as {response}. Is that correct?",
        "responses": {
            "yes": "Great, I've updated your email.",
            "no": "I apologize for the error. Let's try again."
        },
        "next": {
            "yes": "confirm_address",
            "no": "update_email"
        }
    })
    
    # Update phone if needed
    flow.append({
        "id": "update_phone",
        "type": "open_ended",
        "message": "What is your current phone number?",
        "next": "confirm_phone_update"
    })
    
    # Confirm phone update
    flow.append({
        "id": "confirm_phone_update",
        "type": "confirmation",
        "message": "I have your phone number as {response}. Is that correct?",
        "responses": {
            "yes": "Great, I've updated your phone number.",
            "no": "I apologize for the error. Let's try again."
        },
        "next": {
            "yes": "confirm_address",
            "no": "update_phone"
        }
    })
    
    # Get email if not on file
    flow.append({
        "id": "confirm_email",
        "type": "confirmation",
        "message": "I don't have an email address on file for you. Would you like to provide one?",
        "responses": {
            "yes": "Great, what is your email address?",
            "no": "No problem, we can continue without it."
        },
        "next": {
            "yes": "get_email",
            "no": "confirm_address"
        }
    })
    
    # Get email address
    flow.append({
        "id": "get_email",
        "type": "open_ended",
        "message": "What is your email address?",
        "next": "confirm_email_entry"
    })
    
    # Confirm email entry
    flow.append({
        "id": "confirm_email_entry",
        "type": "confirmation",
        "message": "I have your email as {response}. Is that correct?",
        "responses": {
            "yes": "Great, I've added your email.",
            "no": "I apologize for the error. Let's try again."
        },
        "next": {
            "yes": "confirm_address",
            "no": "get_email"
        }
    })
    
    # Confirm address
    has_address = bool(lead.address or (lead.street and lead.city and lead.state and lead.zip_code))
    address_display = lead.address
    if not address_display and lead.street and lead.city and lead.state:
        address_display = f"{lead.street}, {lead.city}, {lead.state} {lead.zip_code if lead.zip_code else ''}"
    
    if has_address:
        flow.append({
            "id": "confirm_address",
            "type": "confirmation",
            "message": f"I have your address as: {address_display}. Is this correct?",
            "responses": {
                "yes": "Thank you for confirming your address.",
                "no": "I apologize for the error. Let's update your address."
            },
            "next": {
                "yes": "tcpa_consent",
                "no": "update_address"
            }
        })
    else:
        flow.append({
            "id": "confirm_address",
            "type": "confirmation",
            "message": "I don't have an address on file for you. Would you like to provide one?",
            "responses": {
                "yes": "Great, what is your address?",
                "no": "No problem, we can continue without it."
            },
            "next": {
                "yes": "get_address",
                "no": "tcpa_consent"
            }
        })
    
    # Update address if needed
    flow.append({
        "id": "update_address",
        "type": "open_ended",
        "message": "What is your current address?",
        "next": "confirm_address_update"
    })
    
    # Confirm address update
    flow.append({
        "id": "confirm_address_update",
        "type": "confirmation",
        "message": "I have your address as {response}. Is that correct?",
        "responses": {
            "yes": "Great, I've updated your address.",
            "no": "I apologize for the error. Let's try again."
        },
        "next": {
            "yes": "tcpa_consent",
            "no": "update_address"
        }
    })
    
    # Get address if not on file
    flow.append({
        "id": "get_address",
        "type": "open_ended",
        "message": "What is your address?",
        "next": "confirm_address_entry"
    })
    
    # Confirm address entry
    flow.append({
        "id": "confirm_address_entry",
        "type": "confirmation",
        "message": "I have your address as {response}. Is that correct?",
        "responses": {
            "yes": "Great, I've added your address.",
            "no": "I apologize for the error. Let's try again."
        },
        "next": {
            "yes": "tcpa_consent",
            "no": "get_address"
        }
    })
    
    # TCPA consent
    flow.append({
        "id": "tcpa_consent",
        "type": "confirmation",
        "message": "Do you consent to receiving calls, texts, and emails about insurance products and services? " +
                   "You can withdraw consent at any time.",
        "responses": {
            "yes": "Thank you for your consent.",
            "no": "That's fine, we'll note your preference."
        },
        "next": "final_confirmation"
    })
    
    # Final confirmation
    flow.append({
        "id": "final_confirmation",
        "type": "confirmation",
        "message": "Thank you for confirming your information. One of our insurance specialists will review your " +
                   "information and get back to you with insurance options that match your needs. " +
                   "Is there anything else you'd like to add before we end the call?",
        "responses": {
            "yes": "What would you like to add?",
            "no": "Great! Thank you for your time today."
        },
        "next": {
            "yes": "additional_info",
            "no": "exit_successful"
        }
    })
    
    # Additional information
    flow.append({
        "id": "additional_info",
        "type": "open_ended",
        "message": "What additional information would you like to provide?",
        "next": "exit_successful"
    })
    
    # Exit messages for different scenarios
    flow.append({
        "id": "exit_successful",
        "type": "message",
        "message": "Thank you for your time today. A specialist will review your information and get back to you soon. Have a great day!",
        "next": "end_call"
    })
    
    flow.append({
        "id": "exit_unavailable",
        "type": "message",
        "message": "Thank you for your time. We'll try to reach out again at a more convenient time. Have a great day!",
        "next": "end_call"
    })
    
    flow.append({
        "id": "exit_callback",
        "type": "message",
        "message": "We'll call you back at the scheduled time. Thank you for your time today. Have a great day!",
        "next": "end_call"
    })
    
    flow.append({
        "id": "end_call",
        "type": "exit",
        "message": "Goodbye!"
    })
    
    return flow

def get_fallback_responses() -> Dict[str, str]:
    """
    Get fallback responses for when the conversation goes off-script.
    
    Returns:
        A dictionary of fallback responses
    """
    return {
        "not_understood": "I'm sorry, I didn't quite catch that. Could you please repeat?",
        "too_many_repeats": "I'm having trouble understanding. Let me connect you with a specialist who can help.",
        "silence": "Hello? Are you still there?",
        "too_long": "That's very detailed information. Let me make a note of that for our specialists.",
        "off_topic": "That's interesting. To stay on topic, let's focus on confirming your information.",
        "angry": "I understand you're frustrated. Would you prefer to speak with a human representative?",
        "inappropriate": "I apologize, but I need to keep this call professional. Let's return to confirming your information."
    }

def get_exit_messages() -> Dict[str, str]:
    """
    Get exit messages for different call outcomes.
    
    Returns:
        A dictionary of exit messages
    """
    return {
        "successful": "Thank you for confirming your information. A specialist will contact you soon with insurance options.",
        "unsuccessful": "I understand this isn't a good time. We'll try to reach you again later.",
        "error": "I apologize, but we're experiencing technical difficulties. We'll try to reach you again soon.",
        "transfer": "I'll transfer you to a specialist who can assist you further. Please hold."
    } 