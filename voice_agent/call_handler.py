"""
Call Handler module for the Voice Agent.

This module provides the integration with the Voice API platform
(either VAPI, Synthflow, or Assistable.AI) to make outbound calls,
process responses, and manage call state.
"""

import os
import sys
import time
import json
import asyncio
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import random

# Add the parent directory to the module search path
sys.path.append(str(Path(__file__).parent.parent))

from database.models import Lead, LeadStatus
from shared import config, utils
from shared.logging_setup import setup_logging, setup_stdlib_logging
from voice_agent.conversation import get_conversation_script

# Set up logging
logger = setup_logging("call_handler")
setup_stdlib_logging()

class CallHandler:
    """
    Handles outbound calls to leads using the configured Voice API.
    This class is responsible for initiating calls, managing the conversation,
    collecting and validating responses, and returning call results.
    """
    
    def __init__(self):
        """Initialize the Call Handler with the appropriate Voice API client"""
        self.provider = config.VOICE_API_PROVIDER
        self.api_config = config.get_voice_api_config()
        
        # Initialize the appropriate API client based on the provider
        if self.provider == "vapi":
            # This would typically import and initialize the VAPI SDK
            # For MVP, we're using a simulated client
            self.client = SimulatedVoiceAPIClient(
                api_key=self.api_config["api_key"],
                base_url=self.api_config.get("base_url")
            )
        elif self.provider == "synthflow":
            # Initialize Synthflow client
            self.client = SimulatedVoiceAPIClient(
                api_key=self.api_config["api_key"],
                base_url=self.api_config.get("base_url")
            )
        elif self.provider == "assistable":
            # Initialize Assistable.AI client
            self.client = SimulatedVoiceAPIClient(
                api_key=self.api_config["api_key"],
                base_url=self.api_config.get("base_url")
            )
        else:
            raise ValueError(f"Unsupported Voice API provider: {self.provider}")
        
        logger.info(f"Call Handler initialized with {self.provider} provider")
    
    async def make_call(self, lead: Lead) -> Dict[str, Any]:
        """
        Make an outbound call to a lead and process the conversation.
        
        Args:
            lead: The lead to call
            
        Returns:
            A dictionary with call results
        """
        # Validate phone number
        if not lead.phone or not utils.is_valid_phone(lead.phone):
            return {
                "success": False,
                "confirmed": False,
                "error": "Invalid or missing phone number",
                "notes": "Could not make call due to invalid phone number"
            }
        
        try:
            # Get the conversation script for this lead
            conversation_script = get_conversation_script(lead)
            
            # Make the call
            logger.info(f"Initiating call to {lead.phone} for lead {lead.id}")
            call_id = await self.client.start_call(lead.phone, conversation_script)
            
            if not call_id:
                return {
                    "success": False,
                    "confirmed": False,
                    "error": "Failed to initiate call",
                    "notes": "Voice API could not initiate the call"
                }
            
            # Wait for the call to complete
            call_result = await self.client.get_call_result(call_id)
            
            # Process the call result
            if call_result["status"] == "completed":
                # Call connected and conversation completed
                logger.info(f"Call completed for lead {lead.id}")
                
                # Extract relevant data from the conversation
                responses = call_result.get("responses", {})
                
                # Check if the lead confirmed their information
                confirmed = self._check_confirmation(responses)
                
                # Extract updated information
                updated_data = self._extract_lead_data(responses)
                
                # Check TCPA consent
                tcpa_consent = self._check_tcpa_consent(responses)
                
                return {
                    "success": True,
                    "confirmed": confirmed,
                    "tcpa_consent": tcpa_consent,
                    "updated_data": updated_data,
                    "voice_data": responses,
                    "recording_url": call_result.get("recording_url"),
                    "notes": call_result.get("notes", "Call completed successfully")
                }
            
            elif call_result["status"] == "no_answer":
                # Call was not answered
                logger.warning(f"No answer for lead {lead.id}")
                return {
                    "success": False,
                    "confirmed": False,
                    "error": "No answer",
                    "notes": "Call was not answered by the lead"
                }
            
            elif call_result["status"] == "busy":
                # Line was busy
                logger.warning(f"Busy signal for lead {lead.id}")
                return {
                    "success": False,
                    "confirmed": False,
                    "error": "Busy",
                    "notes": "Lead's phone line was busy"
                }
            
            elif call_result["status"] == "failed":
                # Call failed for technical reasons
                logger.error(f"Call failed for lead {lead.id}: {call_result.get('error', 'Unknown error')}")
                return {
                    "success": False,
                    "confirmed": False,
                    "error": call_result.get("error", "Call failed"),
                    "notes": f"Call failed: {call_result.get('error', 'Technical failure')}"
                }
            
            else:
                # Unknown status
                logger.warning(f"Unknown call status for lead {lead.id}: {call_result['status']}")
                return {
                    "success": False,
                    "confirmed": False,
                    "error": f"Unknown status: {call_result['status']}",
                    "notes": "Call ended with an unknown status"
                }
        
        except Exception as e:
            logger.error(f"Error during call to lead {lead.id}: {str(e)}")
            return {
                "success": False,
                "confirmed": False,
                "error": str(e),
                "notes": f"Exception during call: {str(e)}"
            }
    
    def _check_confirmation(self, responses: Dict[str, Any]) -> bool:
        """
        Check if the lead confirmed their information during the call.
        
        Args:
            responses: Dictionary of responses from the conversation
            
        Returns:
            True if the lead confirmed their information, False otherwise
        """
        # This logic would depend on the specific conversation flow
        # Check if there's a specific 'confirmation' response
        if "confirmation" in responses:
            confirmation = responses["confirmation"]
            if isinstance(confirmation, bool):
                return confirmation
            elif isinstance(confirmation, str):
                return confirmation.lower() in ['yes', 'true', 'confirm', 'correct']
        
        # Check if there's an 'interested' response
        if "interested" in responses:
            interested = responses["interested"]
            if isinstance(interested, bool):
                return interested
            elif isinstance(interested, str):
                return interested.lower() in ['yes', 'true', 'interested']
        
        # If we have responses for all required fields, consider it confirmed
        required_fields = ["name", "email", "phone", "address"]
        return all(field in responses for field in required_fields)
    
    def _check_tcpa_consent(self, responses: Dict[str, Any]) -> bool:
        """
        Check if the lead gave TCPA consent during the call.
        
        Args:
            responses: Dictionary of responses from the conversation
            
        Returns:
            True if the lead gave TCPA consent, False otherwise
        """
        # Look for specific TCPA consent response
        if "tcpa_consent" in responses:
            consent = responses["tcpa_consent"]
            if isinstance(consent, bool):
                return consent
            elif isinstance(consent, str):
                return consent.lower() in ['yes', 'true', 'agree', 'consent', 'i agree', 'i consent']
        
        # Look for general consent
        if "consent" in responses:
            consent = responses["consent"]
            if isinstance(consent, bool):
                return consent
            elif isinstance(consent, str):
                return consent.lower() in ['yes', 'true', 'agree', 'consent', 'i agree', 'i consent']
        
        # Default to False if no consent information found
        return False
    
    def _extract_lead_data(self, responses: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract updated lead data from conversation responses.
        
        Args:
            responses: Dictionary of responses from the conversation
            
        Returns:
            Dictionary of updated lead data
        """
        updated_data = {}
        
        # Extract name
        if "name" in responses:
            updated_data["name"] = responses["name"]
        elif "full_name" in responses:
            updated_data["name"] = responses["full_name"]
        
        # Extract email
        if "email" in responses:
            email = responses["email"]
            if utils.is_valid_email(email):
                updated_data["email"] = email
        
        # Extract phone
        if "phone" in responses:
            phone = responses["phone"]
            formatted_phone = utils.format_phone_number(phone)
            if utils.is_valid_phone(formatted_phone):
                updated_data["phone"] = formatted_phone
        
        # Extract address
        if "address" in responses:
            updated_data["address"] = responses["address"]
        elif all(k in responses for k in ["street", "city", "state", "zip"]):
            # Construct address from components
            street = responses.get("street", "")
            city = responses.get("city", "")
            state = responses.get("state", "")
            zip_code = responses.get("zip", "")
            
            updated_data["address"] = f"{street}, {city}, {state} {zip_code}"
        
        # Extract address components
        if "street" in responses:
            updated_data["street"] = responses["street"]
        if "city" in responses:
            updated_data["city"] = responses["city"]
        if "state" in responses:
            updated_data["state"] = responses["state"]
        if "zip" in responses or "zip_code" in responses:
            updated_data["zip_code"] = responses.get("zip") or responses.get("zip_code")
        
        # Extract area of interest
        if "area_of_interest" in responses:
            updated_data["area_of_interest"] = responses["area_of_interest"]
        elif "interest" in responses:
            updated_data["area_of_interest"] = responses["interest"]
        
        return updated_data
    
    async def cleanup(self):
        """Clean up resources when shutting down the Call Handler"""
        # Close any open connections or resources
        try:
            await self.client.close()
            logger.info("Call Handler resources cleaned up")
        except Exception as e:
            logger.error(f"Error during Call Handler cleanup: {str(e)}")


class SimulatedVoiceAPIClient:
    """
    Simulated Voice API Client for MVP development.
    
    This class simulates the behavior of a real Voice API client,
    allowing development and testing without an actual voice API integration.
    """
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        """Initialize the simulated client"""
        self.api_key = api_key
        self.base_url = base_url
        self.active_calls = {}
        logger.info(f"Initialized simulated Voice API client")
    
    async def start_call(self, phone_number: str, conversation_script: Dict[str, Any]) -> str:
        """
        Simulate starting an outbound call.
        
        Args:
            phone_number: The phone number to call
            conversation_script: The script for the conversation
            
        Returns:
            A simulated call ID
        """
        # Generate a random call ID
        call_id = f"sim_call_{utils.generate_id()}"
        
        # Store information about this call
        self.active_calls[call_id] = {
            "phone_number": phone_number,
            "script": conversation_script,
            "start_time": time.time(),
            "status": "in_progress"
        }
        
        # For simulation purposes, we'll randomly decide if the call connects
        # In a real implementation, this would initiate an actual API call
        call_outcome = random.choices(
            ["completed", "no_answer", "busy", "failed"],
            weights=[0.7, 0.15, 0.1, 0.05],
            k=1
        )[0]
        
        # For MVP simulation, immediately set the outcome
        # In a real implementation, this would happen asynchronously as the call progresses
        if call_outcome == "completed":
            # Simulate a successful call
            self.active_calls[call_id]["status"] = "completed"
            self.active_calls[call_id]["end_time"] = time.time() + random.uniform(60, 180)
            self.active_calls[call_id]["recording_url"] = f"https://example.com/recordings/{call_id}.mp3"
            
            # Simulate responses
            responses = self._simulate_responses(conversation_script, phone_number)
            self.active_calls[call_id]["responses"] = responses
            
            # Add some random notes
            notes_options = [
                "Lead was very interested in the offer",
                "Lead confirmed all information and gave consent",
                "Lead had some questions but ultimately confirmed",
                "Lead was hesitant but agreed to proceed",
                "Lead was very enthusiastic about the offer"
            ]
            self.active_calls[call_id]["notes"] = random.choice(notes_options)
            
        elif call_outcome == "no_answer":
            # Simulate no answer
            self.active_calls[call_id]["status"] = "no_answer"
            self.active_calls[call_id]["end_time"] = time.time() + random.uniform(20, 40)
            self.active_calls[call_id]["notes"] = "Call was not answered"
            
        elif call_outcome == "busy":
            # Simulate busy signal
            self.active_calls[call_id]["status"] = "busy"
            self.active_calls[call_id]["end_time"] = time.time() + random.uniform(5, 10)
            self.active_calls[call_id]["notes"] = "Line was busy"
            
        else:  # call_outcome == "failed"
            # Simulate a failure
            self.active_calls[call_id]["status"] = "failed"
            self.active_calls[call_id]["end_time"] = time.time() + random.uniform(2, 15)
            
            error_options = [
                "Network error",
                "Call dropped",
                "Audio quality issue",
                "Technical failure",
                "API error"
            ]
            self.active_calls[call_id]["error"] = random.choice(error_options)
            self.active_calls[call_id]["notes"] = f"Call failed: {self.active_calls[call_id]['error']}"
        
        # Simulate network delay
        await asyncio.sleep(1)
        
        logger.info(f"Simulated call {call_id} to {phone_number} initiated with outcome: {call_outcome}")
        return call_id
    
    async def get_call_result(self, call_id: str) -> Dict[str, Any]:
        """
        Get the result of a call.
        
        Args:
            call_id: The ID of the call
            
        Returns:
            A dictionary with the call result
        """
        if call_id not in self.active_calls:
            return {
                "status": "failed",
                "error": "Call not found"
            }
        
        call_data = self.active_calls[call_id]
        
        # If the call is still in progress, wait for it to complete
        if call_data["status"] == "in_progress":
            # In a real implementation, this would poll the API
            # For simulation, we'll just wait a random amount of time
            await asyncio.sleep(2)
        
        result = {
            "status": call_data["status"],
            "start_time": call_data["start_time"],
            "end_time": call_data.get("end_time", time.time())
        }
        
        # Add additional data based on status
        if call_data["status"] == "completed":
            result["responses"] = call_data.get("responses", {})
            result["recording_url"] = call_data.get("recording_url")
            result["notes"] = call_data.get("notes")
        elif call_data["status"] == "failed":
            result["error"] = call_data.get("error", "Unknown error")
            result["notes"] = call_data.get("notes")
        else:
            result["notes"] = call_data.get("notes")
        
        # Simulate network delay
        await asyncio.sleep(0.5)
        
        return result
    
    def _simulate_responses(self, conversation_script: Dict[str, Any], phone_number: str) -> Dict[str, Any]:
        """
        Simulate responses to conversation prompts.
        
        Args:
            conversation_script: The conversation script
            phone_number: The phone number being called
            
        Returns:
            A dictionary of simulated responses
        """
        # In a real implementation, this would parse actual responses from the call
        # For simulation, we'll generate some fake responses
        
        # Randomly decide if the lead confirms or declines
        confirmed = random.choices([True, False], weights=[0.8, 0.2], k=1)[0]
        
        if confirmed:
            # Generate positive responses
            responses = {
                "confirmation": True,
                "interested": True,
                "tcpa_consent": random.choices([True, False], weights=[0.9, 0.1], k=1)[0]
            }
            
            # Generate some fake customer data
            first_names = ["John", "Jane", "Michael", "Emily", "David", "Sarah"]
            last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Davis"]
            
            name = f"{random.choice(first_names)} {random.choice(last_names)}"
            email = f"{name.lower().replace(' ', '.')}@example.com"
            
            domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "aol.com"]
            email = f"{name.lower().replace(' ', '.')}{random.randint(1, 100)}@{random.choice(domains)}"
            
            # Use the provided phone number
            phone = phone_number
            
            # Generate a fake address
            streets = ["123 Main St", "456 Oak Ave", "789 Pine Rd", "321 Elm Blvd", "654 Maple Dr"]
            cities = ["Springfield", "Riverdale", "Oakville", "Pine Hills", "Maplewood"]
            states = ["IL", "CA", "NY", "TX", "FL"]
            zips = ["12345", "23456", "34567", "45678", "56789"]
            
            street = random.choice(streets)
            city = random.choice(cities)
            state = random.choice(states)
            zip_code = random.choice(zips)
            address = f"{street}, {city}, {state} {zip_code}"
            
            # Generate area of interest
            interests = ["Home Insurance", "Auto Insurance", "Life Insurance", "Health Insurance", "Business Insurance"]
            area_of_interest = random.choice(interests)
            
            # Add the data to the responses
            responses.update({
                "name": name,
                "email": email,
                "phone": phone,
                "address": address,
                "street": street,
                "city": city,
                "state": state,
                "zip": zip_code,
                "area_of_interest": area_of_interest
            })
            
        else:
            # Generate negative responses
            responses = {
                "confirmation": False,
                "interested": False,
                "tcpa_consent": False,
                "reason": random.choice([
                    "Not interested at this time",
                    "Already have coverage",
                    "Too expensive",
                    "Will think about it",
                    "Need to discuss with spouse"
                ])
            }
        
        return responses
    
    async def close(self):
        """Close the client and clean up resources"""
        # In a real implementation, this would close connections, etc.
        self.active_calls = {}
        logger.info("Simulated Voice API client closed") 