"""
UI Automation module for interacting with the Lead Hoop portal.

This module uses Playwright to automate browser interactions with the Lead Hoop portal,
including logging in, navigating to the lead entry form, entering lead information,
and submitting the form.
"""

import os
import sys
import time
import asyncio
import random
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import re
import json

# Add the parent directory to the module search path
sys.path.append(str(Path(__file__).parent.parent))

# Import Playwright modules
from playwright.async_api import async_playwright, Playwright, Browser, Page, ElementHandle
from playwright._impl._api_types import Error as PlaywrightError

from database.models import Lead, LeadStatus
from shared import config, utils
from shared.logging_setup import setup_logging, setup_stdlib_logging
from data_entry_agent.lead_hoop_mapper import map_lead_to_form_fields

# Set up logging
logger = setup_logging("ui_automation")
setup_stdlib_logging()

class LeadHoopAutomation:
    """
    Browser automation for the Lead Hoop portal.
    
    This class handles browser automation tasks such as logging in, navigating
    the portal, filling forms, and submitting lead data.
    """
    
    def __init__(self, headless: bool = True, lead_hoop_config: Dict[str, Any] = None):
        """
        Initialize the Lead Hoop automation.
        
        Args:
            headless: Whether to run the browser in headless mode
            lead_hoop_config: Configuration for the Lead Hoop portal
        """
        self.headless = headless
        self.config = lead_hoop_config or config.get_lead_hoop_config()
        self.login_url = self.config.get('url')
        self.username = self.config.get('username')
        self.password = self.config.get('password')
        self.timeout = self.config.get('timeout', 30) * 1000  # Convert to ms
        self.retry_attempts = self.config.get('retry_attempts', 3)
        
        # Playwright objects
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
        # Login state
        self.logged_in = False
        
        logger.info(f"Initialized Lead Hoop automation (headless: {headless})")
    
    async def setup(self):
        """Set up Playwright and launch the browser"""
        try:
            # Launch Playwright
            self.playwright = await async_playwright().start()
            
            # Launch browser (Chromium)
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=['--disable-dev-shm-usage']  # Helpful for Docker environments
            )
            
            # Create a browser context with viewport size appropriate for the portal
            self.context = await self.browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            
            # Create a page
            self.page = await self.context.new_page()
            
            # Set default timeout
            self.page.set_default_timeout(self.timeout)
            
            # Add event listeners for console messages and errors
            self.page.on("console", lambda msg: logger.debug(f"Browser console: {msg.text}"))
            self.page.on("pageerror", lambda err: logger.error(f"Browser page error: {err}"))
            
            logger.info("Browser automation set up successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error setting up browser automation: {str(e)}")
            await self.cleanup()
            raise
    
    async def login(self) -> bool:
        """
        Log in to the Lead Hoop portal.
        
        Returns:
            True if login was successful, False otherwise
        """
        if not self.page:
            logger.error("Cannot log in: Browser not initialized")
            return False
        
        if self.logged_in:
            logger.info("Already logged in to Lead Hoop")
            return True
        
        try:
            logger.info(f"Navigating to Lead Hoop login page: {self.login_url}")
            
            # Navigate to the login page
            await self.page.goto(self.login_url, wait_until="networkidle")
            
            # Check if we're already on the dashboard (already logged in)
            if await self._is_dashboard_page():
                logger.info("Already logged in to Lead Hoop")
                self.logged_in = True
                return True
            
            logger.info("Filling in login credentials")
            
            # Fill in the username/email field
            await self.page.fill('input[name="email"], input[type="email"], input#email', self.username)
            
            # Fill in the password field
            await self.page.fill('input[name="password"], input[type="password"], input#password', self.password)
            
            # Click the login button
            await self.page.click('button[type="submit"], input[type="submit"], .login-button')
            
            # Wait for navigation to complete
            await self.page.wait_for_load_state("networkidle")
            
            # Check if login was successful by looking for dashboard elements
            is_logged_in = await self._is_dashboard_page()
            
            if is_logged_in:
                logger.info("Successfully logged in to Lead Hoop")
                self.logged_in = True
                return True
            else:
                # Check for error messages
                error_text = await self._get_error_message()
                if error_text:
                    logger.error(f"Login failed: {error_text}")
                else:
                    logger.error("Login failed: Unknown error")
                
                return False
        
        except Exception as e:
            logger.error(f"Error logging in to Lead Hoop: {str(e)}")
            return False
    
    async def enter_lead(self, lead: Lead) -> Dict[str, Any]:
        """
        Enter lead data into the Lead Hoop portal.
        
        Args:
            lead: The lead to enter
            
        Returns:
            A dictionary with the result of the data entry
        """
        if not self.page or not self.logged_in:
            logger.error("Cannot enter lead: Not logged in")
            return {
                "success": False,
                "error": "Not logged in to Lead Hoop",
                "notes": "Please log in before attempting to enter leads"
            }
        
        try:
            # Navigate to the lead entry form
            logger.info("Navigating to lead entry form")
            form_navigated = await self._navigate_to_lead_form()
            
            if not form_navigated:
                return {
                    "success": False,
                    "error": "Could not navigate to lead entry form",
                    "notes": "Failed to find or navigate to the lead entry form"
                }
            
            # Map lead data to form fields
            field_mapping = map_lead_to_form_fields(lead)
            
            # Fill in the form fields
            logger.info("Filling lead entry form")
            fields_filled = await self._fill_lead_form(field_mapping)
            
            if not fields_filled:
                return {
                    "success": False,
                    "error": "Could not fill form fields",
                    "notes": "Failed to locate or fill one or more form fields"
                }
            
            # Submit the form
            logger.info("Submitting lead entry form")
            form_submitted = await self._submit_lead_form()
            
            if not form_submitted:
                return {
                    "success": False,
                    "error": "Could not submit form",
                    "notes": "Failed to submit the lead entry form"
                }
            
            # Check for submission success
            submission_success = await self._verify_form_submission()
            
            if submission_success:
                logger.info(f"Successfully entered lead: {lead.name}")
                return {
                    "success": True,
                    "notes": "Lead data successfully entered into Lead Hoop"
                }
            else:
                # Check for error messages
                error_text = await self._get_error_message()
                if error_text:
                    logger.error(f"Lead entry failed: {error_text}")
                    return {
                        "success": False,
                        "error": "Form submission failed",
                        "notes": f"Lead Hoop reported an error: {error_text}"
                    }
                else:
                    logger.error("Lead entry failed: Unknown error")
                    return {
                        "success": False,
                        "error": "Form submission failed",
                        "notes": "Lead entry failed but no specific error message was found"
                    }
        
        except Exception as e:
            logger.error(f"Error entering lead into Lead Hoop: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "notes": f"Exception during lead entry: {str(e)}"
            }
    
    async def refresh_session(self):
        """Refresh the browser session to prevent timeouts"""
        if not self.page:
            logger.error("Cannot refresh session: Browser not initialized")
            return False
        
        try:
            # Navigate to the dashboard or refresh the current page
            if self.logged_in:
                # Navigate to dashboard
                logger.debug("Refreshing session by navigating to dashboard")
                await self._navigate_to_dashboard()
                return True
            else:
                # Just refresh the current page
                logger.debug("Refreshing current page")
                await self.page.reload(wait_until="networkidle")
                return True
        
        except Exception as e:
            logger.error(f"Error refreshing session: {str(e)}")
            return False
    
    async def cleanup(self):
        """Clean up Playwright resources"""
        try:
            if self.page:
                await self.page.close()
                self.page = None
            
            if self.context:
                await self.context.close()
                self.context = None
            
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            
            logger.info("Browser automation resources cleaned up")
        
        except Exception as e:
            logger.error(f"Error cleaning up browser automation: {str(e)}")
    
    async def _is_dashboard_page(self) -> bool:
        """Check if the current page is the dashboard"""
        try:
            # Look for common dashboard elements with appropriate timeout
            dashboard_elements = [
                "text=Dashboard",
                "text=Welcome",
                ".dashboard-header",
                ".admin-panel",
                "nav.sidebar",
                ".user-menu",
                "#dashboard"
            ]
            
            for selector in dashboard_elements:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element:
                        return True
                except:
                    continue
            
            # Check URL for dashboard indicators
            current_url = self.page.url
            if re.search(r'(dashboard|home|admin|main|portal)', current_url.lower()):
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error checking if page is dashboard: {str(e)}")
            return False
    
    async def _navigate_to_dashboard(self) -> bool:
        """Navigate to the dashboard page"""
        try:
            # Common dashboard link selectors
            dashboard_links = [
                "text=Dashboard",
                "a.dashboard-link",
                "a[href*='dashboard']",
                "a[href='/']",
                ".logo a",
                "nav .home-link"
            ]
            
            for selector in dashboard_links:
                try:
                    link = await self.page.wait_for_selector(selector, timeout=5000)
                    if link:
                        await link.click()
                        await self.page.wait_for_load_state("networkidle")
                        return await self._is_dashboard_page()
                except:
                    continue
            
            # Try navigating directly to a known dashboard URL
            dashboard_url = self.login_url.replace('/login', '/dashboard')
            await self.page.goto(dashboard_url, wait_until="networkidle")
            return await self._is_dashboard_page()
        
        except Exception as e:
            logger.error(f"Error navigating to dashboard: {str(e)}")
            return False
    
    async def _navigate_to_lead_form(self) -> bool:
        """Navigate to the lead entry form page"""
        try:
            # First make sure we're on the dashboard
            if not await self._is_dashboard_page():
                if not await self._navigate_to_dashboard():
                    logger.error("Could not navigate to dashboard")
                    return False
            
            # Look for links to lead forms
            lead_form_links = [
                "text=Add Lead",
                "text=New Lead",
                "text=Create Lead",
                "a[href*='lead/add']",
                "a[href*='lead/create']",
                "a[href*='lead/new']",
                "button:has-text('Add Lead')",
                ".new-lead-button"
            ]
            
            for selector in lead_form_links:
                try:
                    link = await self.page.wait_for_selector(selector, timeout=5000)
                    if link:
                        await link.click()
                        await self.page.wait_for_load_state("networkidle")
                        
                        # Verify we're on the lead form page
                        if await self._is_lead_form_page():
                            logger.info("Successfully navigated to lead entry form")
                            return True
                except:
                    continue
            
            logger.error("Could not find lead entry form link")
            return False
        
        except Exception as e:
            logger.error(f"Error navigating to lead form: {str(e)}")
            return False
    
    async def _is_lead_form_page(self) -> bool:
        """Check if the current page is the lead entry form"""
        try:
            # Look for form elements that would indicate a lead entry form
            form_elements = [
                "form.lead-form",
                "form[action*='lead']",
                "h1:has-text('New Lead')",
                "h1:has-text('Add Lead')",
                "h1:has-text('Create Lead')",
                "form input[name='name'], form input[name='lead_name']",
                "form input[name='email'], form input[type='email']",
                "form input[name='phone'], form input[type='tel']"
            ]
            
            for selector in form_elements:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element:
                        return True
                except:
                    continue
            
            # Check URL for lead form indicators
            current_url = self.page.url
            if re.search(r'(lead/add|lead/create|lead/new|add_lead|create_lead)', current_url.lower()):
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error checking if page is lead form: {str(e)}")
            return False
    
    async def _fill_lead_form(self, field_mapping: Dict[str, Any]) -> bool:
        """
        Fill in the lead entry form with the provided field values.
        
        Args:
            field_mapping: Mapping of form field selectors to values
            
        Returns:
            True if all fields were filled successfully, False otherwise
        """
        try:
            # Fill in each field in the mapping
            for field_selector, value in field_mapping.items():
                if isinstance(value, str) and value.strip():
                    # Text fields
                    try:
                        await self.page.fill(field_selector, value)
                        logger.debug(f"Filled field '{field_selector}' with value '{value}'")
                    except Exception as e:
                        logger.warning(f"Failed to fill field '{field_selector}': {str(e)}")
                        # Try clicking the field first, then filling
                        try:
                            await self.page.click(field_selector)
                            await self.page.fill(field_selector, value)
                            logger.debug(f"Filled field '{field_selector}' after clicking")
                        except:
                            logger.error(f"Could not fill field '{field_selector}' even after clicking")
                            return False
                
                elif isinstance(value, bool):
                    # Checkboxes
                    try:
                        if value:
                            # Only check if True, leave unchecked if False
                            await self.page.check(field_selector)
                            logger.debug(f"Checked field '{field_selector}'")
                        else:
                            await self.page.uncheck(field_selector)
                            logger.debug(f"Unchecked field '{field_selector}'")
                    except Exception as e:
                        logger.warning(f"Failed to set checkbox '{field_selector}': {str(e)}")
                        return False
                
                elif isinstance(value, dict) and "type" in value and value["type"] == "select":
                    # Dropdown select
                    try:
                        await self.page.select_option(field_selector, value=value.get("value"))
                        logger.debug(f"Selected option '{value.get('value')}' in field '{field_selector}'")
                    except Exception as e:
                        logger.warning(f"Failed to select option in '{field_selector}': {str(e)}")
                        return False
                
                elif isinstance(value, dict) and "type" in value and value["type"] == "radio":
                    # Radio button
                    try:
                        radio_selector = f"{field_selector}[value='{value.get('value')}']"
                        await self.page.check(radio_selector)
                        logger.debug(f"Selected radio option '{value.get('value')}' for '{field_selector}'")
                    except Exception as e:
                        logger.warning(f"Failed to select radio option for '{field_selector}': {str(e)}")
                        return False
            
            logger.info("Successfully filled all form fields")
            return True
        
        except Exception as e:
            logger.error(f"Error filling lead form: {str(e)}")
            return False
    
    async def _submit_lead_form(self) -> bool:
        """Submit the lead entry form"""
        try:
            # Look for submit buttons
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Submit')",
                "button:has-text('Save')",
                "button:has-text('Add Lead')",
                "button:has-text('Create Lead')",
                ".submit-button",
                ".save-button",
                "form .btn-primary"
            ]
            
            for selector in submit_selectors:
                try:
                    button = await self.page.wait_for_selector(selector, timeout=5000)
                    if button:
                        # Click the button and wait for network activity to complete
                        await button.click()
                        await self.page.wait_for_load_state("networkidle")
                        logger.info("Form submitted")
                        return True
                except:
                    continue
            
            logger.error("Could not find form submit button")
            return False
        
        except Exception as e:
            logger.error(f"Error submitting lead form: {str(e)}")
            return False
    
    async def _verify_form_submission(self) -> bool:
        """Verify that the form was submitted successfully"""
        try:
            # Look for success indicators
            success_selectors = [
                ".alert-success",
                ".success-message",
                "text=Lead created successfully",
                "text=Lead added successfully",
                "text=Lead saved successfully",
                ".toast-success"
            ]
            
            for selector in success_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=10000)
                    if element:
                        logger.info("Form submission verified successful")
                        return True
                except:
                    continue
            
            # Check if we were redirected to a listing page or dashboard
            if (await self._is_dashboard_page() or 
                re.search(r'(lead/list|leads|all_leads)', self.page.url.lower())):
                logger.info("Redirected to dashboard or lead listing after submission")
                return True
            
            # Check for error messages
            error_text = await self._get_error_message()
            if error_text:
                logger.error(f"Form submission failed with error: {error_text}")
                return False
            
            logger.warning("Could not verify form submission success or failure")
            return False
        
        except Exception as e:
            logger.error(f"Error verifying form submission: {str(e)}")
            return False
    
    async def _get_error_message(self) -> Optional[str]:
        """Get error message from the page, if any"""
        try:
            # Common error message selectors
            error_selectors = [
                ".alert-danger",
                ".alert-error",
                ".error-message",
                ".form-error",
                ".validation-error",
                ".toast-error",
                "#error-message",
                "form .text-danger",
                "[role='alert']"
            ]
            
            for selector in error_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=1000)
                    if element:
                        error_text = await element.text_content()
                        if error_text and error_text.strip():
                            return error_text.strip()
                except:
                    continue
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting error message: {str(e)}")
            return None 