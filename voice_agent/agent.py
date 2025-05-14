"""
Voice Agent for making outbound calls to leads.

This agent polls the shared data store for leads with status 'Pending',
initiates outbound calls, collects and confirms information, and updates
the lead status in the database.
"""

import os
import sys
import time
import signal
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import random
from pathlib import Path

# Add the parent directory to the module search path
sys.path.append(str(Path(__file__).parent.parent))

from database.models import get_session, Lead, LeadStatus
from shared import config, utils
from shared.logging_setup import setup_logging, setup_stdlib_logging
from voice_agent.call_handler import CallHandler

# Set up logging
logger = setup_logging("voice_agent")
setup_stdlib_logging()

class VoiceAgent:
    """
    Voice Agent for processing leads via outbound calls.
    
    This agent continuously polls the database for leads with 'Pending' status,
    initiates calls using the configured Voice API, and updates lead status
    based on call outcomes.
    """
    
    def __init__(self):
        """Initialize the Voice Agent"""
        self.running = False
        self.call_handler = CallHandler()
        logger.info("Voice Agent initialized")
    
    async def find_pending_leads(self, limit: int = 10) -> List[Lead]:
        """
        Find leads with 'Pending' status that are ready to be called.
        
        Args:
            limit: Maximum number of leads to retrieve
            
        Returns:
            List of leads ready for calling
        """
        session = get_session()
        try:
            # Query for leads with Pending status
            leads = session.query(Lead) \
                .filter(Lead.status == LeadStatus.PENDING) \
                .order_by(Lead.created_at.asc()) \
                .limit(limit) \
                .all()
            
            return leads
        except Exception as e:
            logger.error(f"Error finding pending leads: {str(e)}")
            return []
        finally:
            session.close()
    
    async def process_lead(self, lead: Lead) -> bool:
        """
        Process a single lead by making an outbound call and updating the lead status.
        
        Args:
            lead: The lead to process
            
        Returns:
            True if processing was successful, False otherwise
        """
        session = get_session()
        try:
            # Mark the lead as being called
            lead.status = LeadStatus.CALLING
            lead.call_attempts += 1
            lead.last_call_timestamp = utils.timestamp()
            lead.log_activity(session, "call_initiated", {"attempt": lead.call_attempts}, "voice_agent")
            session.commit()
            
            logger.info(f"Calling lead: {lead.name} ({lead.phone})")
            
            # Make the call
            start_time = time.time()
            call_result = await self.call_handler.make_call(lead)
            end_time = time.time()
            
            # Update the lead with call results
            lead.call_duration = end_time - start_time
            
            if call_result["success"]:
                # Call connected and completed successfully
                if call_result["confirmed"]:
                    # Lead confirmed information
                    lead.status = LeadStatus.CONFIRMED
                    lead.tcpa_consent = call_result.get("tcpa_consent", lead.tcpa_consent)
                    lead.voice_consent_recording_url = call_result.get("recording_url")
                    
                    # Update lead data from call if provided
                    if "updated_data" in call_result:
                        updated_data = call_result["updated_data"]
                        if "name" in updated_data:
                            lead.name = updated_data["name"]
                        if "email" in updated_data:
                            lead.email = updated_data["email"]
                        if "phone" in updated_data:
                            lead.phone = updated_data["phone"]
                        if "address" in updated_data:
                            lead.address = updated_data["address"]
                        if "area_of_interest" in updated_data:
                            lead.area_of_interest = updated_data["area_of_interest"]
                    
                    # Store voice data
                    lead.voice_data = call_result.get("voice_data", {})
                    
                    lead.call_notes = call_result.get("notes", "Lead confirmed information")
                    lead.log_activity(session, "call_confirmed", call_result, "voice_agent")
                    logger.info(f"Lead confirmed: {lead.name}")
                    
                else:
                    # Lead not interested or declined
                    lead.status = LeadStatus.NOT_INTERESTED
                    lead.call_notes = call_result.get("notes", "Lead not interested")
                    lead.log_activity(session, "call_declined", call_result, "voice_agent")
                    logger.info(f"Lead not interested: {lead.name}")
            else:
                # Call failed
                lead.status = LeadStatus.CALL_FAILED
                lead.call_notes = call_result.get("notes", "Call failed to connect")
                lead.log_activity(session, "call_failed", call_result, "voice_agent")
                logger.warning(f"Call failed for lead: {lead.name} - {call_result.get('error', 'Unknown error')}")
            
            # Save changes
            lead.updated_at = utils.timestamp()
            session.commit()
            
            return True
        
        except Exception as e:
            logger.error(f"Error processing lead {lead.id}: {str(e)}")
            # Try to mark the lead as error
            try:
                lead.status = LeadStatus.ERROR
                lead.call_notes = f"Error during call: {str(e)}"
                lead.log_activity(session, "call_error", {"error": str(e)}, "voice_agent")
                session.commit()
            except Exception:
                logger.error("Failed to update lead status after error")
                session.rollback()
            
            return False
        
        finally:
            session.close()
    
    async def run(self):
        """Run the Voice Agent to process leads continuously"""
        self.running = True
        logger.info("Voice Agent started")
        
        # Register signal handlers for graceful shutdown
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self._handle_shutdown)
        
        try:
            while self.running:
                # Find pending leads
                leads = await self.find_pending_leads(limit=config.MAX_CONCURRENT_CALLS)
                
                if not leads:
                    logger.debug("No pending leads found, waiting...")
                    await asyncio.sleep(config.VOICE_AGENT_POLLING_INTERVAL)
                    continue
                
                logger.info(f"Found {len(leads)} pending leads")
                
                # Process leads concurrently
                tasks = [self.process_lead(lead) for lead in leads]
                results = await asyncio.gather(*tasks)
                
                # Wait before next poll
                await asyncio.sleep(config.VOICE_AGENT_POLLING_INTERVAL)
        
        except Exception as e:
            logger.error(f"Error in Voice Agent main loop: {str(e)}")
        
        finally:
            logger.info("Voice Agent shutting down")
            await self.call_handler.cleanup()
    
    def _handle_shutdown(self, sig, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received shutdown signal {sig}, stopping Voice Agent")
        self.running = False

async def main():
    """Main function to run the Voice Agent"""
    agent = VoiceAgent()
    await agent.run()

if __name__ == "__main__":
    # Run the agent
    asyncio.run(main()) 