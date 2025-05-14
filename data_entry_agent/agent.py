"""
Data Entry Agent for automating lead data entry into Lead Hoop.

This agent polls the shared data store for leads with status 'Confirmed',
initiates browser automation sessions, enters the data into the Lead Hoop portal,
and updates lead status in the database.
"""

import os
import sys
import time
import signal
import asyncio
import random
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path

# Add the parent directory to the module search path
sys.path.append(str(Path(__file__).parent.parent))

from database.models import get_session, Lead, LeadStatus
from shared import config, utils
from shared.logging_setup import setup_logging, setup_stdlib_logging
from data_entry_agent.ui_automation import LeadHoopAutomation

# Set up logging
logger = setup_logging("data_entry_agent")
setup_stdlib_logging()

class DataEntryAgent:
    """
    Data Entry Agent for automating lead entry into Lead Hoop.
    
    This agent continuously polls the database for leads with 'Confirmed' status,
    uses browser automation to enter the data into the Lead Hoop portal, and
    updates lead status based on entry outcomes.
    """
    
    def __init__(self):
        """Initialize the Data Entry Agent"""
        self.running = False
        self.automation = None
        logger.info("Data Entry Agent initialized")
    
    async def setup(self):
        """Set up resources for the Data Entry Agent"""
        # Initialize the browser automation
        try:
            self.automation = LeadHoopAutomation(
                headless=config.HEADLESS_BROWSER,
                lead_hoop_config=config.get_lead_hoop_config()
            )
            await self.automation.setup()
            logger.info("Browser automation set up successfully")
        except Exception as e:
            logger.error(f"Error setting up browser automation: {str(e)}")
            raise
    
    async def find_confirmed_leads(self, limit: int = 5) -> List[Lead]:
        """
        Find leads with 'Confirmed' status that are ready for data entry.
        
        Args:
            limit: Maximum number of leads to retrieve
            
        Returns:
            List of leads ready for data entry
        """
        session = get_session()
        try:
            # Query for leads with Confirmed status
            leads = session.query(Lead) \
                .filter(Lead.status == LeadStatus.CONFIRMED) \
                .order_by(Lead.updated_at.asc()) \
                .limit(limit) \
                .all()
            
            return leads
        except Exception as e:
            logger.error(f"Error finding confirmed leads: {str(e)}")
            return []
        finally:
            session.close()
    
    async def process_lead(self, lead: Lead) -> bool:
        """
        Process a single lead by entering data into Lead Hoop.
        
        Args:
            lead: The lead to process
            
        Returns:
            True if processing was successful, False otherwise
        """
        session = get_session()
        try:
            # Mark the lead as being processed
            lead.status = LeadStatus.ENTRY_IN_PROGRESS
            lead.entry_attempts += 1
            lead.last_entry_timestamp = utils.timestamp()
            lead.log_activity(session, "entry_initiated", {"attempt": lead.entry_attempts}, "data_entry_agent")
            session.commit()
            
            logger.info(f"Processing lead for data entry: {lead.name} (ID: {lead.id})")
            
            # Enter the data
            start_time = time.time()
            entry_result = await self.automation.enter_lead(lead)
            end_time = time.time()
            
            # Update the lead with entry results
            lead.entry_duration = end_time - start_time
            
            if entry_result["success"]:
                # Data entry was successful
                lead.status = LeadStatus.ENTERED
                lead.entry_notes = entry_result.get("notes", "Data entered successfully")
                lead.log_activity(session, "entry_completed", entry_result, "data_entry_agent")
                logger.info(f"Data entry successful for lead: {lead.name}")
            else:
                # Data entry failed
                lead.status = LeadStatus.ENTRY_FAILED
                lead.entry_notes = entry_result.get("notes", f"Data entry failed: {entry_result.get('error', 'Unknown error')}")
                lead.log_activity(session, "entry_failed", entry_result, "data_entry_agent")
                logger.warning(f"Data entry failed for lead: {lead.name} - {entry_result.get('error', 'Unknown error')}")
            
            # Save changes
            lead.updated_at = utils.timestamp()
            session.commit()
            
            return entry_result["success"]
        
        except Exception as e:
            logger.error(f"Error processing lead {lead.id}: {str(e)}")
            # Try to mark the lead as error
            try:
                lead.status = LeadStatus.ERROR
                lead.entry_notes = f"Error during data entry: {str(e)}"
                lead.log_activity(session, "entry_error", {"error": str(e)}, "data_entry_agent")
                session.commit()
            except Exception:
                logger.error("Failed to update lead status after error")
                session.rollback()
            
            return False
        
        finally:
            session.close()
    
    async def run(self):
        """Run the Data Entry Agent to process leads continuously"""
        self.running = True
        logger.info("Data Entry Agent started")
        
        # Register signal handlers for graceful shutdown
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self._handle_shutdown)
        
        try:
            # Set up automation
            await self.setup()
            
            # Log in to Lead Hoop
            login_successful = await self.automation.login()
            if not login_successful:
                logger.error("Failed to log in to Lead Hoop. Stopping agent.")
                return
            
            logger.info("Successfully logged in to Lead Hoop")
            
            # Main processing loop
            while self.running:
                # Find confirmed leads
                leads = await self.find_confirmed_leads(limit=config.MAX_CONCURRENT_ENTRIES)
                
                if not leads:
                    logger.debug("No confirmed leads found, waiting...")
                    await asyncio.sleep(config.DATA_ENTRY_AGENT_POLLING_INTERVAL)
                    continue
                
                logger.info(f"Found {len(leads)} confirmed leads")
                
                # Process leads in sequence 
                # (parallel processing could be risky with UI automation)
                for lead in leads:
                    if not self.running:
                        break
                    
                    await self.process_lead(lead)
                    
                    # Small delay between leads to avoid overloading the browser
                    await asyncio.sleep(1)
                
                # Wait before next poll
                await asyncio.sleep(config.DATA_ENTRY_AGENT_POLLING_INTERVAL)
                
                # Periodically refresh the session to avoid timeouts
                if random.random() < 0.1:  # ~10% chance each cycle
                    logger.debug("Refreshing Lead Hoop session")
                    try:
                        await self.automation.refresh_session()
                    except Exception as e:
                        logger.error(f"Error refreshing session: {str(e)}")
                        # Try to re-login if session refresh fails
                        try:
                            await self.automation.login()
                        except Exception as login_error:
                            logger.error(f"Failed to re-login: {str(login_error)}")
        
        except Exception as e:
            logger.error(f"Error in Data Entry Agent main loop: {str(e)}")
        
        finally:
            logger.info("Data Entry Agent shutting down")
            if self.automation:
                await self.automation.cleanup()
    
    def _handle_shutdown(self, sig, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received shutdown signal {sig}, stopping Data Entry Agent")
        self.running = False

async def main():
    """Main function to run the Data Entry Agent"""
    agent = DataEntryAgent()
    await agent.run()

if __name__ == "__main__":
    # Run the agent
    asyncio.run(main()) 