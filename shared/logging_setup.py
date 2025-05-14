"""
Logging setup for the Voice AI Agent system.

This module provides functions to set up logging for different components
of the system, ensuring consistent logging format and behavior.
"""

import os
import sys
import logging
import logging.handlers
import traceback
from pathlib import Path
from typing import Optional, Dict, Any

from shared import config

# Ensure the log directory exists
LOG_DIR = Path(__file__).parent.parent / "logs"
if not LOG_DIR.exists():
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def get_log_level() -> int:
    """
    Get the log level from configuration.
    
    Returns:
        The logging level as an integer.
    """
    level_name = config.LOG_LEVEL.upper()
    return getattr(logging, level_name, logging.INFO)


def setup_logging(name: str) -> logging.Logger:
    """
    Set up a logger with the given name.
    
    Args:
        name: The name of the logger, typically the module or component name.
        
    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger(name)
    
    # Clear existing handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # Set the log level
    logger.setLevel(get_log_level())
    
    # Create file handler
    log_file = LOG_DIR / f"{name}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Set formatter for handlers
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def setup_stdlib_logging():
    """
    Set up logging for standard library and third-party modules.
    
    This is useful to capture logs from libraries like requests, sqlalchemy, etc.
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(get_log_level())
    
    # Create file handler for third-party logs
    log_file = LOG_DIR / "third_party.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Set formatter for handler
    file_handler.setFormatter(formatter)
    
    # Add handler to root logger
    root_logger.addHandler(file_handler)
    
    # Set specific levels for noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('playwright').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)


def log_exception(logger: logging.Logger, exc: Exception, context: Optional[Dict[str, Any]] = None):
    """
    Log an exception with full traceback and optional context.
    
    Args:
        logger: The logger to use
        exc: The exception to log
        context: Optional context information about when the exception occurred
    """
    exc_info = sys.exc_info()
    trace = traceback.format_exception(*exc_info)
    
    # Format the context information
    context_str = ""
    if context:
        context_str = " | Context: " + ", ".join([f"{k}={v}" for k, v in context.items()])
    
    # Log the exception with context
    logger.error(f"Exception: {exc}{context_str}\n{''.join(trace)}") 