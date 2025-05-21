#!/usr/bin/env python
"""
Main entry point for the Multi-Agent Lead Processing System.
"""

import os
import sys
import asyncio
import argparse
import subprocess
import threading
from pathlib import Path

# Add the project directory to the path
sys.path.append(str(Path(__file__).resolve().parent))

from app.main import main as run_application
from app.api.api import start_api_server
from app.config.settings import APP_NAME, APP_VERSION


def start_api_server_thread(host, port):
    """
    Start the API server in a separate thread.
    
    Parameters:
    -----------
    host : str
        The host to bind to.
    port : int
        The port to listen on.
    """
    # Import API server here to avoid circular imports
    from app.api.api import start_api_server
    
    # Start the API server
    print(f"Starting API server on {host}:{port}")
    start_api_server(host=host, port=port)


def main():
    """
    Main entry point.
    """
    parser = argparse.ArgumentParser(description=f"{APP_NAME} v{APP_VERSION}")
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
    
    # Print banner
    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║  {APP_NAME} v{APP_VERSION}                        ║
    ║                                                           ║
    ║  Multi-Agent System for Lead Processing with:             ║
    ║   - Voice AI Agent                                        ║
    ║   - Data Entry Agent                                      ║
    ║   - Shared Data Store                                     ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # If API only mode, just start the API server
    if args.api_only:
        print(f"Running in API-only mode on {args.api_host}:{args.api_port}")
        start_api_server(host=args.api_host, port=args.api_port)
        return
    
    # If running the main application
    if args.api:
        # Start API server in a thread
        api_thread = threading.Thread(
            target=start_api_server_thread, 
            args=(args.api_host, args.api_port),
            daemon=True
        )
        api_thread.start()
    
    # Set up arguments for the main application
    app_args = []
    if args.reset_db:
        app_args.append("--reset-db")
    if args.no_headless:
        app_args.append("--no-headless")
    if args.status_only:
        app_args.append("--status-only")
    
    app_args.extend([
        "--voice-batch", str(args.voice_batch),
        "--entry-batch", str(args.entry_batch),
        "--csv-interval", str(args.csv_interval)
    ])
    
    # Run the actual application
    application_args = argparse.Namespace(
        reset_db=args.reset_db,
        no_headless=args.no_headless,
        voice_batch=args.voice_batch,
        entry_batch=args.entry_batch,
        csv_interval=args.csv_interval,
        status_only=args.status_only
    )
    
    # Run the application
    asyncio.run(run_application())
    
    # If we're running the API server in a thread, wait for it to complete
    if args.api and api_thread.is_alive():
        print("Waiting for API server to shutdown...")
        api_thread.join(timeout=5)


if __name__ == "__main__":
    main() 