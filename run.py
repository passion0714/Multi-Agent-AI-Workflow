#!/usr/bin/env python3
"""
Main script to run the entire Voice AI Agent system.

This script initializes the database, starts the API server,
launches the Voice Agent and Data Entry Agent, and manages
the system as a whole.
"""

import os
import sys
import asyncio
import argparse
import signal
import threading
from pathlib import Path

# Add the current directory to the module search path
sys.path.append(str(Path(__file__).parent))

from database.models import init_db
from shared import config
from shared.logging_setup import setup_logging, setup_stdlib_logging
from shared.api import start_api
from voice_agent.agent import main as voice_agent_main
from data_entry_agent.agent import main as data_entry_agent_main

# Set up logging
logger = setup_logging("system")
setup_stdlib_logging()

# Flag for graceful shutdown
running = True

def handle_shutdown(sig, frame):
    """Handle shutdown signals"""
    global running
    logger.info(f"Received shutdown signal {sig}, stopping system")
    running = False

def run_api_server():
    """Run the API server in a separate thread"""
    logger.info("Starting API server")
    start_api()

async def main():
    """Main function to run the entire system"""
    global running
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run the Voice AI Agent system")
    parser.add_argument('--api-only', action='store_true', help='Run only the API server')
    parser.add_argument('--voice-only', action='store_true', help='Run only the Voice Agent')
    parser.add_argument('--data-entry-only', action='store_true', help='Run only the Data Entry Agent')
    parser.add_argument('--no-api', action='store_true', help='Do not run the API server')
    parser.add_argument('--init-db', action='store_true', help='Initialize the database before starting')
    args = parser.parse_args()
    
    # Register signal handlers for graceful shutdown
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, handle_shutdown)
    
    try:
        # Initialize database if requested
        if args.init_db:
            logger.info("Initializing database")
            init_db()
            logger.info("Database initialized")
        
        # Determine which components to run
        run_api = not args.no_api and not (args.voice_only or args.data_entry_only)
        run_voice = not args.api_only and not args.data_entry_only
        run_data_entry = not args.api_only and not args.voice_only
        
        # Start API server in a separate thread if requested
        api_thread = None
        if run_api:
            api_thread = threading.Thread(target=run_api_server)
            api_thread.daemon = True
            api_thread.start()
            logger.info("API server started in background thread")
        
        # Start agents as tasks if requested
        tasks = []
        
        if run_voice:
            logger.info("Starting Voice Agent")
            voice_task = asyncio.create_task(voice_agent_main())
            tasks.append(voice_task)
        
        if run_data_entry:
            logger.info("Starting Data Entry Agent")
            data_entry_task = asyncio.create_task(data_entry_agent_main())
            tasks.append(data_entry_task)
        
        # Wait for tasks to complete or for shutdown signal
        if tasks:
            try:
                done, pending = await asyncio.wait(
                    tasks,
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Check if any tasks completed with an exception
                for task in done:
                    if task.exception():
                        logger.error(f"Task failed with exception: {task.exception()}")
                
                # Cancel any pending tasks on shutdown
                for task in pending:
                    task.cancel()
                
                # Wait for tasks to be cancelled
                if pending:
                    await asyncio.wait(pending, timeout=5)
            
            except asyncio.CancelledError:
                logger.info("Main task cancelled")
            
            finally:
                # Ensure all tasks are cancelled
                for task in tasks:
                    if not task.done():
                        task.cancel()
        
        else:
            # If only running API, wait for Ctrl+C
            logger.info("System running. Press Ctrl+C to stop.")
            while running:
                await asyncio.sleep(1)
    
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
    
    finally:
        logger.info("System shutting down")
        # API server thread will automatically terminate when main thread exits

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main()) 