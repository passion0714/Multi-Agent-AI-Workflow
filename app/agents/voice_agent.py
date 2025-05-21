import os
import sys
import time
import json
import asyncio
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import tempfile

# Add parent directory to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from app.database.models import Lead, LeadStatus
from app.database.repository import LeadRepository
from app.utils.s3_utils import s3_manager
from app.config.settings import (
    ASSISTABLE_API_KEY, 
    ASSISTABLE_API_URL,
    MAX_CONCURRENT_CALLS, 
    CALL_RETRY_ATTEMPTS,
    CALL_TIMEOUT_SECONDS,
    TCPA_COMPLIANCE_TEXT
)
from loguru import logger


class AssistableAIClient:
    """
    Client for interacting with the Assistable.AI API.
    """
    
    def __init__(self, api_key: str = None, api_url: str = None):
        """
        Initialize the Assistable.AI client.
        
        Parameters:
        -----------
        api_key : str, optional
            API key for Assistable.AI. If not provided, uses the one from settings.
        api_url : str, optional
            Base URL for the Assistable.AI API. If not provided, uses the one from settings.
        """
        self.api_key = api_key or ASSISTABLE_API_KEY
        self.api_url = api_url or ASSISTABLE_API_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def make_call(self, phone_number: str, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make an outbound call to a lead using Assistable.AI.
        
        Parameters:
        -----------
        phone_number : str
            The phone number to call.
        lead_data : Dict[str, Any]
            Data about the lead, used to populate the call script.
            
        Returns:
        --------
        Dict[str, Any]
            Response from the Assistable.AI API.
        """
        try:
            # Construct the payload for the call
            payload = {
                "phone_number": phone_number,
                "call_script": self._generate_call_script(lead_data),
                "voice_id": "en-US-Neural2-F",  # Female voice
                "record_call": True,
                "callback_url": "https://your-webhook-url.com/call-events",  # Replace with your webhook URL
                "metadata": {
                    "lead_id": lead_data.get("id"),
                    "type": "lead_verification"
                }
            }
            
            # Make the API call
            response = requests.post(
                f"{self.api_url}/calls",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "call_id": response.json().get("call_id"),
                    "status": response.json().get("status")
                }
            else:
                logger.error(f"Failed to make call: {response.text}")
                return {
                    "success": False,
                    "error": response.text,
                    "status_code": response.status_code
                }
                
        except Exception as e:
            logger.error(f"Error making call: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_call_status(self, call_id: str) -> Dict[str, Any]:
        """
        Check the status of a call.
        
        Parameters:
        -----------
        call_id : str
            The ID of the call to check.
            
        Returns:
        --------
        Dict[str, Any]
            Call status details.
        """
        try:
            response = requests.get(
                f"{self.api_url}/calls/{call_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "status": response.json().get("status"),
                    "details": response.json()
                }
            else:
                logger.error(f"Failed to get call status: {response.text}")
                return {
                    "success": False,
                    "error": response.text,
                    "status_code": response.status_code
                }
                
        except Exception as e:
            logger.error(f"Error getting call status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def download_recording(self, call_id: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Download the recording of a call.
        
        Parameters:
        -----------
        call_id : str
            The ID of the call to download.
        output_path : Optional[str], default=None
            Path where to save the recording. If None, a temporary file will be created.
            
        Returns:
        --------
        Dict[str, Any]
            Download status and file path.
        """
        try:
            # If no output path provided, create a temporary file
            if not output_path:
                temp_dir = tempfile.gettempdir()
                output_path = os.path.join(temp_dir, f"call_{call_id}.mp3")
            
            # Get recording URL
            response = requests.get(
                f"{self.api_url}/calls/{call_id}/recording",
                headers=self.headers
            )
            
            if response.status_code == 200:
                recording_url = response.json().get("recording_url")
                
                if not recording_url:
                    return {
                        "success": False,
                        "error": "No recording URL available",
                        "file_path": None
                    }
                
                # Download the recording
                download_response = requests.get(recording_url)
                
                if download_response.status_code == 200:
                    with open(output_path, "wb") as f:
                        f.write(download_response.content)
                    
                    return {
                        "success": True,
                        "file_path": output_path,
                        "file_size": len(download_response.content)
                    }
                else:
                    logger.error(f"Failed to download recording: {download_response.text}")
                    return {
                        "success": False,
                        "error": download_response.text,
                        "status_code": download_response.status_code,
                        "file_path": None
                    }
            else:
                logger.error(f"Failed to get recording URL: {response.text}")
                return {
                    "success": False,
                    "error": response.text,
                    "status_code": response.status_code,
                    "file_path": None
                }
                
        except Exception as e:
            logger.error(f"Error downloading recording: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "file_path": None
            }
    
    def _generate_call_script(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a call script for Assistable.AI based on lead data.
        
        Parameters:
        -----------
        lead_data : Dict[str, Any]
            Data about the lead.
            
        Returns:
        --------
        Dict[str, Any]
            Call script in the format expected by Assistable.AI.
        """
        first_name = lead_data.get("firstname", "")
        last_name = lead_data.get("lastname", "")
        full_name = f"{first_name} {last_name}".strip()
        
        # Build the script with conversation flow
        script = {
            "intro": f"Hello, may I speak with {full_name}? This is calling from IEIM Corporation about your recent inquiry regarding educational opportunities.",
            
            "verify_identity": [
                {
                    "message": f"Great! To confirm I'm speaking with the right person, could you please confirm your email address?",
                    "responses": {
                        "confirmed": {"next": "verify_address"},
                        "incorrect": {"message": "I apologize for the confusion. Let me double-check our records.", "next": "end_call"},
                        "unknown": {"message": "No problem. Let's move forward.", "next": "verify_address"}
                    }
                }
            ],
            
            "verify_address": [
                {
                    "message": f"Thank you. And I have your address as {lead_data.get('address', '')}, {lead_data.get('city', '')}, {lead_data.get('state', '')} {lead_data.get('zip', '')}. Is that correct?",
                    "responses": {
                        "yes": {"next": "verify_education"},
                        "no": {"message": "I'll make a note to update our records. What is your current address?", "next": "collect_address"}
                    }
                }
            ],
            
            "collect_address": [
                {
                    "message": "Thank you for that updated information. I've made a note of your new address.",
                    "next": "verify_education"
                }
            ],
            
            "verify_education": [
                {
                    "message": f"I see you're interested in {lead_data.get('education_level', 'higher education')}. Is that still the case?",
                    "responses": {
                        "yes": {"next": "area_of_interest"},
                        "no": {"message": "What level of education are you interested in now?", "next": "collect_education"}
                    }
                }
            ],
            
            "collect_education": [
                {
                    "message": "Thank you for updating that information.",
                    "next": "area_of_interest"
                }
            ],
            
            "area_of_interest": [
                {
                    "message": "What specific area of study are you most interested in pursuing?",
                    "next": "tcpa_compliance"
                }
            ],
            
            "tcpa_compliance": [
                {
                    "message": f"{TCPA_COMPLIANCE_TEXT}",
                    "responses": {
                        "yes": {"message": "Thank you for confirming.", "next": "conclusion"},
                        "no": {"message": "That's absolutely fine. We can still proceed with your request.", "next": "conclusion"}
                    }
                }
            ],
            
            "conclusion": [
                {
                    "message": "Thank you for confirming your information. We will match you with educational institutions that offer programs in your area of interest. You can expect to hear from them soon. Do you have any questions before we conclude this call?",
                    "responses": {
                        "yes": {"message": "I'll note your question for our enrollment specialists, who will address it when they contact you.", "next": "end_call"},
                        "no": {"next": "end_call"}
                    }
                }
            ],
            
            "end_call": [
                {
                    "message": "Thank you for your time today. Have a great day!"
                }
            ]
        }
        
        return script


class VoiceAgent:
    """
    Agent for making outbound calls to leads using Assistable.AI.
    """
    
    def __init__(self):
        """
        Initialize the Voice Agent.
        """
        self.assistable_client = AssistableAIClient()
        self.active_calls = {}  # Tracks currently active calls
    
    async def run(self, batch_size: int = 5, run_once: bool = False):
        """
        Run the Voice Agent to process leads.
        
        Parameters:
        -----------
        batch_size : int, default=5
            Number of leads to process in each batch.
        run_once : bool, default=False
            If True, process one batch and exit. If False, run continuously.
        """
        logger.info(f"Starting Voice Agent (batch size: {batch_size}, run_once: {run_once})")
        
        if not ASSISTABLE_API_KEY:
            logger.error("ASSISTABLE_API_KEY is not set. Voice Agent cannot start.")
            return
        
        try:
            running = True
            while running:
                # Get pending leads
                leads = LeadRepository.get_pending_leads_for_calling(limit=batch_size)
                
                if not leads:
                    logger.info("No pending leads found for calling.")
                    if run_once:
                        break
                    
                    # Wait before checking again
                    await asyncio.sleep(30)
                    continue
                
                logger.info(f"Found {len(leads)} leads for calling")
                
                # Process each lead
                tasks = []
                for lead in leads:
                    # Skip if we've reached the maximum concurrent calls
                    if len(self.active_calls) >= MAX_CONCURRENT_CALLS:
                        logger.info(f"Reached maximum concurrent calls limit ({MAX_CONCURRENT_CALLS})")
                        break
                    
                    # Create a task for processing this lead
                    task = asyncio.create_task(self.process_lead(lead))
                    tasks.append(task)
                
                # Wait for all tasks to complete
                if tasks:
                    await asyncio.gather(*tasks)
                
                # Exit if run_once is True
                if run_once:
                    running = False
                else:
                    # Wait before processing the next batch
                    await asyncio.sleep(5)
                
        except Exception as e:
            logger.error(f"Error in Voice Agent run loop: {str(e)}")
    
    async def process_lead(self, lead: Lead) -> bool:
        """
        Process a single lead by making an outbound call.
        
        Parameters:
        -----------
        lead : Lead
            The lead to process.
            
        Returns:
        --------
        bool
            True if the lead was processed successfully, False otherwise.
        """
        logger.info(f"Processing lead {lead.id}: {lead.firstname} {lead.lastname}")
        
        try:
            # Update lead status to CALLING
            LeadRepository.update_lead_status(
                lead.id, 
                LeadStatus.CALLING,
                {
                    "call_initiated_at": datetime.utcnow(),
                    "call_attempts": lead.call_attempts + 1
                }
            )
            
            # Convert lead to dictionary for API call
            lead_data = {
                "id": lead.id,
                "firstname": lead.firstname,
                "lastname": lead.lastname,
                "email": lead.email,
                "phone1": lead.phone1,
                "address": lead.address,
                "address2": lead.address2,
                "city": lead.city,
                "state": lead.state,
                "zip": lead.zip,
                "education_level": lead.education_level,
                "area_of_study": lead.area_of_study
            }
            
            # Make the call
            call_response = self.assistable_client.make_call(lead.phone1, lead_data)
            
            if not call_response["success"]:
                logger.error(f"Failed to initiate call for lead {lead.id}: {call_response.get('error')}")
                
                # Update lead status to CALL_FAILED
                LeadRepository.update_lead_status(
                    lead.id, 
                    LeadStatus.CALL_FAILED,
                    {
                        "call_completed_at": datetime.utcnow(),
                        "last_error": call_response.get("error", "Failed to initiate call")
                    }
                )
                
                # Log the call
                LeadRepository.log_call(
                    lead.id,
                    {
                        "completed_at": datetime.utcnow(),
                        "status": "failed",
                        "error": call_response.get("error", "Failed to initiate call")
                    }
                )
                
                return False
            
            # Call was initiated successfully
            call_id = call_response["call_id"]
            self.active_calls[call_id] = lead.id
            
            # Monitor the call until completion
            completed = await self._monitor_call(call_id, lead.id)
            
            # Clean up
            if call_id in self.active_calls:
                del self.active_calls[call_id]
            
            return completed
            
        except Exception as e:
            logger.error(f"Error processing lead {lead.id}: {str(e)}")
            
            # Update lead status to CALL_FAILED
            LeadRepository.update_lead_status(
                lead.id, 
                LeadStatus.CALL_FAILED,
                {
                    "call_completed_at": datetime.utcnow(),
                    "last_error": str(e)
                }
            )
            
            # Log the call
            LeadRepository.log_call(
                lead.id,
                {
                    "completed_at": datetime.utcnow(),
                    "status": "error",
                    "error": str(e)
                }
            )
            
            return False
    
    async def _monitor_call(self, call_id: str, lead_id: int) -> bool:
        """
        Monitor a call until it completes or times out.
        
        Parameters:
        -----------
        call_id : str
            The ID of the call to monitor.
        lead_id : int
            The ID of the lead being called.
            
        Returns:
        --------
        bool
            True if the call completed successfully, False otherwise.
        """
        start_time = datetime.utcnow()
        timeout = start_time + timedelta(seconds=CALL_TIMEOUT_SECONDS)
        
        while datetime.utcnow() < timeout:
            # Check call status
            status_response = self.assistable_client.get_call_status(call_id)
            
            if not status_response["success"]:
                logger.error(f"Failed to get status for call {call_id}: {status_response.get('error')}")
                await asyncio.sleep(5)
                continue
            
            status = status_response["status"]
            logger.info(f"Call {call_id} status: {status}")
            
            if status in ["completed", "failed", "no-answer", "busy", "canceled"]:
                # Call has ended, process the results
                return await self._process_call_results(call_id, lead_id, status_response)
            
            # Wait before checking again
            await asyncio.sleep(5)
        
        # Call timed out
        logger.warning(f"Call {call_id} timed out after {CALL_TIMEOUT_SECONDS} seconds")
        
        # Update lead status to CALL_FAILED
        LeadRepository.update_lead_status(
            lead_id, 
            LeadStatus.CALL_FAILED,
            {
                "call_completed_at": datetime.utcnow(),
                "last_error": f"Call timed out after {CALL_TIMEOUT_SECONDS} seconds"
            }
        )
        
        # Log the call
        LeadRepository.log_call(
            lead_id,
            {
                "completed_at": datetime.utcnow(),
                "status": "timeout",
                "error": f"Call timed out after {CALL_TIMEOUT_SECONDS} seconds"
            }
        )
        
        return False
    
    async def _process_call_results(self, call_id: str, lead_id: int, status_response: Dict[str, Any]) -> bool:
        """
        Process the results of a completed call.
        
        Parameters:
        -----------
        call_id : str
            The ID of the call.
        lead_id : int
            The ID of the lead.
        status_response : Dict[str, Any]
            Response from the call status check.
            
        Returns:
        --------
        bool
            True if the call was successful and the lead was updated, False otherwise.
        """
        status = status_response["status"]
        details = status_response.get("details", {})
        call_data = {}
        
        if status == "completed":
            # Extract information from the call
            transcript = details.get("transcript", {})
            responses = transcript.get("responses", {})
            
            # Extract confirmed information from responses
            confirmed_email = None
            confirmed_address = None
            confirmed_area_of_interest = None
            tcpa_accepted = False
            
            # Parse through responses to extract confirmed information
            # This would depend on the actual response format from Assistable.AI
            # Below is a placeholder implementation
            for section, response in responses.items():
                if section == "verify_identity" and response.get("confirmed"):
                    confirmed_email = response.get("value")
                
                elif section == "collect_address":
                    confirmed_address = response.get("value")
                
                elif section == "area_of_interest":
                    confirmed_area_of_interest = response.get("value")
                
                elif section == "tcpa_compliance" and response.get("response") == "yes":
                    tcpa_accepted = True
            
            # Determine if the lead confirmed interest
            interested = True  # Default to interested unless explicitly not interested
            for section, response in responses.items():
                if section in ["verify_education", "area_of_interest"] and response.get("response") == "no":
                    interested = False
                    break
            
            # Download the call recording
            recording_response = await asyncio.to_thread(
                self.assistable_client.download_recording, 
                call_id
            )
            
            if recording_response["success"]:
                # Upload recording to S3
                file_path = recording_response["file_path"]
                lead = LeadRepository.get_lead_by_id(lead_id)
                
                s3_response = await asyncio.to_thread(
                    s3_manager.upload_recording,
                    lead.phone1,
                    file_path,
                    lead.call_initiated_at or datetime.utcnow()
                )
                
                if s3_response["success"]:
                    call_data["recording_url"] = s3_response["url"]
                
                # Delete the temporary file
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary recording file: {str(e)}")
            
            # Calculate call duration
            call_duration = None
            if details.get("start_time") and details.get("end_time"):
                start_time = datetime.fromisoformat(details["start_time"].replace("Z", "+00:00"))
                end_time = datetime.fromisoformat(details["end_time"].replace("Z", "+00:00"))
                call_duration = (end_time - start_time).total_seconds()
            
            # Update call data
            call_data.update({
                "completed_at": datetime.utcnow(),
                "status": "completed",
                "duration": call_duration,
                "notes": json.dumps(responses)
            })
            
            # Log the call
            LeadRepository.log_call(lead_id, call_data)
            
            # Update lead status based on interest
            if interested:
                # Update lead with confirmed information
                LeadRepository.update_lead_status(
                    lead_id, 
                    LeadStatus.CONFIRMED,
                    {
                        "confirmed_email": confirmed_email,
                        "confirmed_address": confirmed_address,
                        "confirmed_area_of_interest": confirmed_area_of_interest,
                        "tcpa_accepted": tcpa_accepted,
                        "call_completed_at": datetime.utcnow(),
                        "call_duration": call_duration,
                        "call_recording_url": call_data.get("recording_url"),
                        "call_notes": json.dumps(responses)
                    }
                )
                
                logger.info(f"Lead {lead_id} confirmed and ready for data entry")
                return True
            else:
                # Lead is not interested
                LeadRepository.update_lead_status(
                    lead_id, 
                    LeadStatus.NOT_INTERESTED,
                    {
                        "call_completed_at": datetime.utcnow(),
                        "call_duration": call_duration,
                        "call_recording_url": call_data.get("recording_url"),
                        "call_notes": json.dumps(responses)
                    }
                )
                
                logger.info(f"Lead {lead_id} is not interested")
                return True
        
        else:
            # Call failed in some way
            LeadRepository.update_lead_status(
                lead_id, 
                LeadStatus.CALL_FAILED,
                {
                    "call_completed_at": datetime.utcnow(),
                    "last_error": f"Call failed with status: {status}"
                }
            )
            
            # Log the call
            LeadRepository.log_call(
                lead_id,
                {
                    "completed_at": datetime.utcnow(),
                    "status": status,
                    "error": f"Call failed with status: {status}"
                }
            )
            
            logger.warning(f"Call {call_id} for lead {lead_id} failed with status: {status}")
            return False


async def main():
    """
    Main function to run the Voice Agent.
    """
    # Configure logging
    log_file = "logs/voice_agent.log"
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logger.add(log_file, rotation="10 MB", retention="7 days")
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Voice Agent for contacting leads")
    parser.add_argument("--batch-size", type=int, default=5, help="Number of leads to process in each batch")
    parser.add_argument("--run-once", action="store_true", help="Process one batch and exit")
    args = parser.parse_args()
    
    try:
        # Initialize and run the Voice Agent
        agent = VoiceAgent()
        await agent.run(batch_size=args.batch_size, run_once=args.run_once)
    except KeyboardInterrupt:
        logger.info("Voice Agent stopped by user")
    except Exception as e:
        logger.error(f"Voice Agent error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main()) 