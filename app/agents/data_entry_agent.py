import os
import sys
import time
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import random

# Add parent directory to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from app.database.models import Lead, LeadStatus
from app.database.repository import LeadRepository
from app.config.settings import (
    LEADHOOP_PORTAL_URL,
    LEADHOOP_USERNAME,
    LEADHOOP_PASSWORD,
    MAX_CONCURRENT_DATA_ENTRIES,
    ENTRY_RETRY_ATTEMPTS,
    ENTRY_TIMEOUT_SECONDS
)
from loguru import logger

# Import Playwright
from playwright.async_api import async_playwright, Playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError


class LeadHoopClient:
    """
    Client for interacting with the LeadHoop portal using Playwright.
    """
    
    def __init__(self, headless: bool = True):
        """
        Initialize the LeadHoop client.
        
        Parameters:
        -----------
        headless : bool, optional
            Whether to run the browser in headless mode. Default is True.
        """
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
    
    async def __aenter__(self):
        """
        Context manager entry - initialize Playwright and browser.
        """
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit - close browser and Playwright.
        """
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def login(self, page: Page) -> bool:
        """
        Log in to the LeadHoop portal.
        
        Parameters:
        -----------
        page : Page
            Playwright page object.
            
        Returns:
        --------
        bool
            True if login successful, False otherwise.
        """
        try:
            # Check if credentials are set
            if not LEADHOOP_USERNAME or not LEADHOOP_PASSWORD:
                logger.error("LeadHoop credentials are not set")
                return False
            
            # Navigate to login page (this might need adjustment based on the actual portal)
            await page.goto(LEADHOOP_PORTAL_URL, wait_until="networkidle")
            
            # Check if we're already logged in (this depends on the portal's behavior)
            if "login" not in page.url.lower() and "sign in" not in await page.title().lower():
                logger.info("Already logged in to LeadHoop")
                return True
            
            # Find and fill login form
            await page.fill("input[name='username'], input[name='email']", LEADHOOP_USERNAME)
            await page.fill("input[name='password']", LEADHOOP_PASSWORD)
            
            # Click login button
            await page.click("button[type='submit'], input[type='submit']")
            
            # Wait for navigation to complete
            await page.wait_for_load_state("networkidle")
            
            # Verify login was successful
            if "login" in page.url.lower() or "sign in" in await page.title().lower():
                logger.error("Login failed - still on login page")
                return False
            
            logger.info("Successfully logged in to LeadHoop")
            return True
            
        except Exception as e:
            logger.error(f"Error logging in to LeadHoop: {str(e)}")
            return False
    
    async def submit_lead(self, page: Page, lead: Lead) -> Dict[str, Any]:
        """
        Submit a lead to the LeadHoop portal.
        
        Parameters:
        -----------
        page : Page
            Playwright page object.
        lead : Lead
            The lead to submit.
            
        Returns:
        --------
        Dict[str, Any]
            Result of the submission.
        """
        try:
            # Navigate to the submission form
            await page.goto(LEADHOOP_PORTAL_URL, wait_until="networkidle")
            
            # Wait for the form to be visible
            form_selector = "form"  # Adjust based on the actual portal
            await page.wait_for_selector(form_selector, state="visible")
            
            # Fill in the form fields based on lead data
            await self._fill_lead_form(page, lead)
            
            # Take a screenshot for verification (optional)
            screenshot_path = f"logs/screenshots/lead_{lead.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            await page.screenshot(path=screenshot_path)
            
            # Submit the form
            await page.click("button[type='submit']")
            
            # Wait for submission to complete (adjust based on portal behavior)
            await page.wait_for_load_state("networkidle")
            
            # Check for success indicators
            success = await self._verify_submission_success(page)
            
            if success:
                logger.info(f"Successfully submitted lead {lead.id} to LeadHoop")
                return {
                    "success": True,
                    "lead_id": lead.id,
                    "screenshot": screenshot_path,
                    "message": "Lead submitted successfully"
                }
            else:
                error_message = await self._extract_error_message(page)
                logger.error(f"Failed to submit lead {lead.id}: {error_message}")
                return {
                    "success": False,
                    "lead_id": lead.id,
                    "screenshot": screenshot_path,
                    "error": error_message
                }
                
        except Exception as e:
            logger.error(f"Error submitting lead {lead.id}: {str(e)}")
            
            # Try to take a screenshot of the error state
            try:
                error_screenshot = f"logs/screenshots/error_lead_{lead.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                os.makedirs(os.path.dirname(error_screenshot), exist_ok=True)
                await page.screenshot(path=error_screenshot)
            except:
                error_screenshot = None
            
            return {
                "success": False,
                "lead_id": lead.id,
                "screenshot": error_screenshot,
                "error": str(e)
            }
    
    async def _fill_lead_form(self, page: Page, lead: Lead) -> None:
        """
        Fill in the LeadHoop form with lead data.
        
        Parameters:
        -----------
        page : Page
            Playwright page object.
        lead : Lead
            The lead whose data to fill in.
        """
        # Map the lead fields to form field selectors
        # This mapping will need to be adjusted based on the actual portal's form
        form_mapping = {
            # Basic information
            "input[name='first_name']": lead.firstname,
            "input[name='last_name']": lead.lastname,
            "input[name='email']": lead.confirmed_email or lead.email,
            "input[name='phone']": lead.confirmed_phone or lead.phone1,
            
            # Address
            "input[name='address']": lead.confirmed_address or lead.address,
            "input[name='address2']": lead.address2,
            "input[name='city']": lead.city,
            "input[name='state']": lead.state,
            "input[name='zip']": lead.zip,
            
            # Additional fields
            "input[name='education_level']": lead.education_level,
            "select[name='area_of_study']": lead.confirmed_area_of_interest or lead.area_of_study,
            "input[name='grad_year']": lead.grad_year,
            "input[name='start_date']": lead.start_date,
        }
        
        # Fill in the form fields
        for selector, value in form_mapping.items():
            if value:
                try:
                    if selector.startswith("select"):
                        # Handle dropdown fields
                        await page.select_option(selector, value)
                    elif selector.startswith("input[type='checkbox']"):
                        # Handle checkbox fields
                        if value.lower() in ["yes", "true", "1"]:
                            await page.check(selector)
                    else:
                        # Handle regular input fields
                        await page.fill(selector, str(value))
                except Exception as e:
                    logger.warning(f"Could not fill field {selector}: {str(e)}")
        
        # Handle checkbox for TCPA acceptance
        if lead.tcpa_accepted:
            try:
                # Look for common TCPA checkbox selectors
                tcpa_selectors = [
                    "input[name='tcpa_consent']",
                    "input[name='tcpa_opt_in']",
                    "input[id*='tcpa']",
                    "input[id*='consent']",
                    "input[type='checkbox']"
                ]
                
                for selector in tcpa_selectors:
                    if await page.query_selector(selector):
                        await page.check(selector)
                        break
            except Exception as e:
                logger.warning(f"Could not check TCPA consent: {str(e)}")
    
    async def _verify_submission_success(self, page: Page) -> bool:
        """
        Verify if the form submission was successful.
        
        Parameters:
        -----------
        page : Page
            Playwright page object.
            
        Returns:
        --------
        bool
            True if submission was successful, False otherwise.
        """
        # Look for success indicators (adjust based on the portal)
        success_indicators = [
            "thank you",
            "success",
            "submitted",
            "received",
            "confirmation"
        ]
        
        try:
            # Check URL for success indicators
            for indicator in success_indicators:
                if indicator in page.url.lower():
                    return True
            
            # Check page content for success messages
            page_content = await page.content()
            for indicator in success_indicators:
                if indicator in page_content.lower():
                    return True
            
            # Look for success elements
            success_selectors = [
                ".success-message",
                ".alert-success",
                ".confirmation",
                "h1:has-text('Thank You')",
                ".success"
            ]
            
            for selector in success_selectors:
                if await page.query_selector(selector):
                    return True
            
            # If we couldn't find any success indicators, check for error indicators
            error_indicators = [
                "error",
                "failed",
                "invalid",
                "problem",
                "incorrect"
            ]
            
            for indicator in error_indicators:
                if indicator in page_content.lower():
                    return False
            
            # If we couldn't determine success or failure, default to assuming it worked
            # This might need adjustment based on the portal's behavior
            return True
            
        except Exception as e:
            logger.error(f"Error verifying submission success: {str(e)}")
            return False
    
    async def _extract_error_message(self, page: Page) -> str:
        """
        Extract error message from the page after a failed submission.
        
        Parameters:
        -----------
        page : Page
            Playwright page object.
            
        Returns:
        --------
        str
            Extracted error message, or a generic message if none found.
        """
        try:
            # Look for common error message selectors
            error_selectors = [
                ".error-message",
                ".alert-danger",
                ".form-error",
                ".validation-summary-errors",
                ".error"
            ]
            
            for selector in error_selectors:
                element = await page.query_selector(selector)
                if element:
                    message = await element.text_content()
                    if message.strip():
                        return message.strip()
            
            # If no specific error message found, return generic one
            return "Form submission failed without a specific error message"
            
        except Exception as e:
            logger.error(f"Error extracting error message: {str(e)}")
            return "Error extracting error message from page"


class DataEntryAgent:
    """
    Agent for submitting leads to the LeadHoop portal.
    """
    
    def __init__(self, headless: bool = True):
        """
        Initialize the Data Entry Agent.
        
        Parameters:
        -----------
        headless : bool, optional
            Whether to run the browser in headless mode. Default is True.
        """
        self.headless = headless
        self.active_entries = 0  # Tracks currently active data entry processes
    
    async def run(self, batch_size: int = 3, run_once: bool = False):
        """
        Run the Data Entry Agent to process leads.
        
        Parameters:
        -----------
        batch_size : int, default=3
            Number of leads to process in each batch.
        run_once : bool, default=False
            If True, process one batch and exit. If False, run continuously.
        """
        logger.info(f"Starting Data Entry Agent (batch size: {batch_size}, run_once: {run_once})")
        
        if not LEADHOOP_USERNAME or not LEADHOOP_PASSWORD:
            logger.error("LeadHoop credentials are not set. Data Entry Agent cannot start.")
            return
        
        try:
            running = True
            while running:
                # Get confirmed leads
                leads = LeadRepository.get_confirmed_leads_for_entry(limit=batch_size)
                
                if not leads:
                    logger.info("No confirmed leads found for data entry.")
                    if run_once:
                        break
                    
                    # Wait before checking again
                    await asyncio.sleep(30)
                    continue
                
                logger.info(f"Found {len(leads)} leads for data entry")
                
                # Process leads in parallel, up to the concurrent limit
                tasks = []
                for lead in leads:
                    # Skip if we've reached the maximum concurrent entries
                    if self.active_entries >= MAX_CONCURRENT_DATA_ENTRIES:
                        logger.info(f"Reached maximum concurrent entries limit ({MAX_CONCURRENT_DATA_ENTRIES})")
                        break
                    
                    # Create a task for processing this lead
                    task = asyncio.create_task(self.process_lead(lead))
                    tasks.append(task)
                    self.active_entries += 1
                
                # Wait for all tasks to complete
                if tasks:
                    await asyncio.gather(*tasks)
                    self.active_entries = 0  # Reset the counter after all tasks are done
                
                # Exit if run_once is True
                if run_once:
                    running = False
                else:
                    # Wait before processing the next batch
                    await asyncio.sleep(5)
                
        except Exception as e:
            logger.error(f"Error in Data Entry Agent run loop: {str(e)}")
    
    async def process_lead(self, lead: Lead) -> bool:
        """
        Process a single lead by submitting it to the LeadHoop portal.
        
        Parameters:
        -----------
        lead : Lead
            The lead to process.
            
        Returns:
        --------
        bool
            True if the lead was processed successfully, False otherwise.
        """
        logger.info(f"Processing lead {lead.id} for data entry: {lead.firstname} {lead.lastname}")
        
        try:
            # Update lead status to ENTRY_IN_PROGRESS
            LeadRepository.update_lead_status(
                lead.id, 
                LeadStatus.ENTRY_IN_PROGRESS,
                {
                    "entry_initiated_at": datetime.utcnow(),
                    "entry_attempts": lead.entry_attempts + 1
                }
            )
            
            # Initialize the LeadHoop client
            async with LeadHoopClient(headless=self.headless) as client:
                page = await client.context.new_page()
                
                # Login to LeadHoop
                login_success = await client.login(page)
                if not login_success:
                    logger.error(f"Failed to log in to LeadHoop for lead {lead.id}")
                    
                    # Update lead status to ENTRY_FAILED
                    LeadRepository.update_lead_status(
                        lead.id, 
                        LeadStatus.ENTRY_FAILED,
                        {
                            "entry_completed_at": datetime.utcnow(),
                            "last_error": "Failed to log in to LeadHoop portal"
                        }
                    )
                    
                    # Log the entry attempt
                    LeadRepository.log_entry(
                        lead.id,
                        {
                            "completed_at": datetime.utcnow(),
                            "status": "login_failed",
                            "error": "Failed to log in to LeadHoop portal"
                        }
                    )
                    
                    return False
                
                # Submit the lead
                start_time = datetime.utcnow()
                result = await client.submit_lead(page, lead)
                end_time = datetime.utcnow()
                
                # Calculate duration
                duration = (end_time - start_time).total_seconds()
                
                if result["success"]:
                    # Update lead status to ENTERED
                    LeadRepository.update_lead_status(
                        lead.id, 
                        LeadStatus.ENTERED,
                        {
                            "entry_completed_at": datetime.utcnow(),
                            "entry_duration": duration,
                            "entry_notes": result.get("message", "Lead submitted successfully")
                        }
                    )
                    
                    # Log the entry
                    LeadRepository.log_entry(
                        lead.id,
                        {
                            "completed_at": datetime.utcnow(),
                            "status": "completed",
                            "duration": duration,
                            "notes": result.get("message", "Lead submitted successfully")
                        }
                    )
                    
                    logger.info(f"Successfully submitted lead {lead.id} to LeadHoop")
                    return True
                else:
                    # Update lead status to ENTRY_FAILED
                    LeadRepository.update_lead_status(
                        lead.id, 
                        LeadStatus.ENTRY_FAILED,
                        {
                            "entry_completed_at": datetime.utcnow(),
                            "entry_duration": duration,
                            "last_error": result.get("error", "Unknown error during submission")
                        }
                    )
                    
                    # Log the entry attempt
                    LeadRepository.log_entry(
                        lead.id,
                        {
                            "completed_at": datetime.utcnow(),
                            "status": "failed",
                            "duration": duration,
                            "error": result.get("error", "Unknown error during submission")
                        }
                    )
                    
                    logger.error(f"Failed to submit lead {lead.id} to LeadHoop: {result.get('error')}")
                    return False
            
        except Exception as e:
            logger.error(f"Error processing lead {lead.id} for data entry: {str(e)}")
            
            # Update lead status to ENTRY_FAILED
            LeadRepository.update_lead_status(
                lead.id, 
                LeadStatus.ENTRY_FAILED,
                {
                    "entry_completed_at": datetime.utcnow(),
                    "last_error": str(e)
                }
            )
            
            # Log the entry attempt
            LeadRepository.log_entry(
                lead.id,
                {
                    "completed_at": datetime.utcnow(),
                    "status": "error",
                    "error": str(e)
                }
            )
            
            return False
        finally:
            # Ensure active entries count is decremented even if an exception occurred
            self.active_entries -= 1


async def main():
    """
    Main function to run the Data Entry Agent.
    """
    # Configure logging
    log_file = "logs/data_entry_agent.log"
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logger.add(log_file, rotation="10 MB", retention="7 days")
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Data Entry Agent for submitting leads")
    parser.add_argument("--batch-size", type=int, default=3, help="Number of leads to process in each batch")
    parser.add_argument("--run-once", action="store_true", help="Process one batch and exit")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    args = parser.parse_args()
    
    try:
        # Install browsers if needed (first run only)
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                # Just to check if browsers are installed
                pass
        except Exception as e:
            if "Executable doesn't exist" in str(e):
                logger.info("Installing Playwright browsers...")
                import subprocess
                subprocess.run(["playwright", "install", "chromium"])
            else:
                logger.warning(f"Playwright check error: {str(e)}")
        
        # Initialize and run the Data Entry Agent
        agent = DataEntryAgent(headless=args.headless)
        await agent.run(batch_size=args.batch_size, run_once=args.run_once)
    except KeyboardInterrupt:
        logger.info("Data Entry Agent stopped by user")
    except Exception as e:
        logger.error(f"Data Entry Agent error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main()) 