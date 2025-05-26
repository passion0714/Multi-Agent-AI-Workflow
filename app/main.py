import os
import sys
import asyncio
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import signal
import threading
import time

# Add parent directory to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.agents.voice_agent import VoiceAgent
from app.agents.data_entry_agent import DataEntryAgent
from app.utils.csv_processor import CSVProcessor
from app.database.repository import LeadRepository
from app.database.init_db import init_db
from app.config.settings import (
    APP_NAME,
    APP_VERSION,
    LOG_LEVEL,
    CSV_IMPORT_DIRECTORY,
    MAX_CONCURRENT_CALLS,
    MAX_CONCURRENT_DATA_ENTRIES
)
from loguru import logger


class ApplicationManager:
    """
    Main application manager that coordinates all components.
    """
    
    def __init__(self):
        """
        Initialize the Application Manager.
        """
        self.voice_agent = None
        self.data_entry_agent = None
        self.csv_processor_thread = None
        self.running = False
        self.startup_time = datetime.utcnow()
    
    async def initialize(self, reset_db: bool = False, headless: bool = True):
        """
        Initialize all components.
        
        Parameters:
        -----------
        reset_db : bool, optional
            Whether to reset the database. Default is False.
        headless : bool, optional
            Whether to run browsers in headless mode. Default is True.
        """
        logger.info(f"Initializing {APP_NAME} v{APP_VERSION}")
        
        # Initialize database
        if reset_db:
            logger.info("Resetting database...")
            init_db(drop_all=True)
        else:
            # Just ensure tables exist
            init_db(drop_all=False)
        
        # Create agents
        logger.info("Creating agents...")
        self.voice_agent = VoiceAgent()
        self.data_entry_agent = DataEntryAgent(headless=headless)
        
        # Set running flag
        self.running = True
        
        logger.info("Initialization complete")
    
    def start_csv_processor(self, interval: int = 60):
        """
        Start the CSV processor in a separate thread.
        
        Parameters:
        -----------
        interval : int, optional
            Interval in seconds between CSV processing runs. Default is 60.
        """
        def csv_processor_worker():
            logger.info(f"Starting CSV processor (interval: {interval}s)")
            
            while self.running:
                try:
                    # Check for new CSV files and process them
                    logger.info("Checking for new CSV files...")
                    results = CSVProcessor.process_new_csv_files()
                    
                    if results["total_files"] > 0:
                        logger.info(f"Processed {results['processed_files']}/{results['total_files']} files, imported {results['imported_leads']}/{results['total_leads']} leads")
                    
                    # Wait for the next interval
                    for _ in range(interval):
                        if not self.running:
                            break
                        time.sleep(1)
                        
                except Exception as e:
                    logger.error(f"Error in CSV processor: {str(e)}")
                    time.sleep(10)  # Wait a bit longer on error
        
        # Start the thread
        self.csv_processor_thread = threading.Thread(target=csv_processor_worker, daemon=True)
        self.csv_processor_thread.start()
        logger.info("CSV processor thread started")
    
    async def start_agents(self, voice_batch_size: int = 5, data_entry_batch_size: int = 3):
        """
        Start the Voice and Data Entry agents.
        
        Parameters:
        -----------
        voice_batch_size : int, optional
            Batch size for the Voice Agent. Default is 5.
        data_entry_batch_size : int, optional
            Batch size for the Data Entry Agent. Default is 3.
        """
        try:
            # Start both agents in parallel
            logger.info("Starting agents...")
            
            voice_task = asyncio.create_task(
                self.voice_agent.run(batch_size=voice_batch_size, run_once=False)
            )
            
            data_entry_task = asyncio.create_task(
                self.data_entry_agent.run(batch_size=data_entry_batch_size, run_once=False)
            )
            
            # Wait for both tasks to complete (they should run indefinitely until cancelled)
            await asyncio.gather(voice_task, data_entry_task)
            
        except asyncio.CancelledError:
            logger.info("Agents cancelled")
        except Exception as e:
            logger.error(f"Error running agents: {str(e)}")
    
    def stop(self):
        """
        Stop all components gracefully.
        """
        logger.info("Stopping application...")
        self.running = False
        
        # Other cleanup if needed
        
        logger.info("Application stopped")
    
    async def get_system_status(self) -> dict:
        """
        Get the current status of the system.
        
        Returns:
        --------
        dict
            System status information.
        """
        # Get lead statistics
        lead_stats = LeadRepository.get_lead_statistics()
        
        # Calculate uptime
        uptime = datetime.utcnow() - self.startup_time
        uptime_str = str(uptime).split('.')[0]  # Remove microseconds
        
        # Build status
        return {
            "application": f"{APP_NAME} v{APP_VERSION}",
            "status": "running" if self.running else "stopped",
            "uptime": uptime_str,
            "started_at": self.startup_time.isoformat(),
            "lead_stats": lead_stats,
            "csv_processor": {
                "running": self.csv_processor_thread is not None and self.csv_processor_thread.is_alive(),
                "import_directory": CSV_IMPORT_DIRECTORY
            },
            "voice_agent": {
                "running": self.voice_agent is not None,
                "max_concurrent_calls": MAX_CONCURRENT_CALLS,
                "active_calls": len(self.voice_agent.active_calls) if self.voice_agent else 0
            },
            "data_entry_agent": {
                "running": self.data_entry_agent is not None,
                "max_concurrent_entries": MAX_CONCURRENT_DATA_ENTRIES,
                "active_entries": self.data_entry_agent.active_entries if self.data_entry_agent else 0
            }
        }


async def main():
    """
    Main function to run the application.
    """
    # Configure logging
    log_file = "logs/application.log"
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logger.add(log_file, rotation="10 MB", retention="7 days")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description=f"{APP_NAME} - Multi-Agent Lead Processing System")
    parser.add_argument("--reset-db", action="store_true", help="Reset the database on startup")
    parser.add_argument("--no-headless", action="store_true", help="Run browsers in non-headless mode (visible)")
    parser.add_argument("--voice-batch", type=int, default=5, help="Batch size for the Voice Agent")
    parser.add_argument("--entry-batch", type=int, default=3, help="Batch size for the Data Entry Agent")
    parser.add_argument("--csv-interval", type=int, default=60, help="Interval in seconds between CSV processing runs")
    parser.add_argument("--api", action="store_true", help="Run the API server")
    parser.add_argument("--api-only", action="store_true", help="Run only the API server without the main application")
    parser.add_argument("--api-host", type=str, default="0.0.0.0", help="Host for the API server")
    parser.add_argument("--api-port", type=int, default=8000, help="Port for the API server")
    parser.add_argument("--status-only", action="store_true", help="Just print system status and exit")
    args = parser.parse_args()
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        app_manager.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and initialize the application manager
    app_manager = ApplicationManager()
    
    # If status only, just print status and exit
    if args.status_only:
        await app_manager.initialize(reset_db=False, headless=True)
        status = await app_manager.get_system_status()
        print("\nSystem Status:")
        for key, value in status.items():
            if isinstance(value, dict):
                print(f"\n{key.upper()}:")
                for k, v in value.items():
                    print(f"  {k}: {v}")
            else:
                print(f"{key}: {value}")
        return
    
    try:
        # Initialize the system
        await app_manager.initialize(reset_db=args.reset_db, headless=not args.no_headless)
        
        # Start the CSV processor
        app_manager.start_csv_processor(interval=args.csv_interval)
        
        # Start the agents
        await app_manager.start_agents(
            voice_batch_size=args.voice_batch,
            data_entry_batch_size=args.entry_batch
        )
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
    finally:
        app_manager.stop()


if __name__ == "__main__":
    asyncio.run(main()) 