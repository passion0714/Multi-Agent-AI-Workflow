"""
Utilities module for the Voice AI Agent system.

This module provides common utility functions used across different
components of the system.
"""

import os
import re
import json
import time
import uuid
import hashlib
import random
import string
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union, Tuple


def timestamp() -> datetime:
    """
    Get the current timestamp with UTC timezone.
    
    Returns:
        Current datetime with UTC timezone
    """
    return datetime.now(timezone.utc)


def iso_timestamp() -> str:
    """
    Get the current timestamp as an ISO 8601 string.
    
    Returns:
        Current timestamp as ISO 8601 string
    """
    return timestamp().isoformat()


def generate_id(prefix: str = '') -> str:
    """
    Generate a unique ID with an optional prefix.
    
    Args:
        prefix: Optional prefix to add to the ID
        
    Returns:
        A unique ID string
    """
    random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    time_part = int(time.time())
    if prefix:
        return f"{prefix}_{time_part}_{random_part}"
    return f"{time_part}_{random_part}"


def clean_phone_number(phone: str) -> str:
    """
    Clean a phone number by removing non-digit characters and 
    ensuring proper formatting.
    
    Args:
        phone: The phone number to clean
        
    Returns:
        Cleaned phone number as a string
    """
    # Remove non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Handle US numbers
    if len(digits_only) == 10:
        return digits_only
    elif len(digits_only) == 11 and digits_only.startswith('1'):
        return digits_only[1:]
    
    # Return as is if not a standard format
    return digits_only


def format_phone_for_display(phone: str) -> str:
    """
    Format a phone number for display in a user-friendly format.
    
    Args:
        phone: The phone number to format
        
    Returns:
        Formatted phone number as a string (e.g., (555) 123-4567)
    """
    clean = clean_phone_number(phone)
    
    if len(clean) == 10:
        return f"({clean[0:3]}) {clean[3:6]}-{clean[6:10]}"
    
    # Return as is if not a standard format
    return phone


def mask_sensitive_data(data: Dict[str, Any], fields_to_mask: List[str]) -> Dict[str, Any]:
    """
    Mask sensitive data in a dictionary.
    
    Args:
        data: Dictionary containing potentially sensitive data
        fields_to_mask: List of field names to mask
        
    Returns:
        Dictionary with sensitive fields masked
    """
    masked_data = data.copy()
    for field in fields_to_mask:
        if field in masked_data and masked_data[field]:
            if isinstance(masked_data[field], str) and len(masked_data[field]) > 4:
                # Keep last 4 characters, mask the rest
                masked_data[field] = '*' * (len(masked_data[field]) - 4) + masked_data[field][-4:]
            else:
                masked_data[field] = '****'
    
    return masked_data


def safe_json_loads(text: str, default: Any = None) -> Any:
    """
    Safely parse JSON string, returning a default value on error.
    
    Args:
        text: JSON string to parse
        default: Default value to return if parsing fails
        
    Returns:
        Parsed JSON object or default value
    """
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default or {}


def safe_json_dumps(obj: Any, default: str = '{}') -> str:
    """
    Safely convert object to JSON string, returning a default value on error.
    
    Args:
        obj: Object to convert to JSON
        default: Default string to return if conversion fails
        
    Returns:
        JSON string or default value
    """
    try:
        return json.dumps(obj)
    except (TypeError, OverflowError, ValueError):
        return default


def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    Truncate text to maximum length, adding a suffix if truncated.
    
    Args:
        text: Text to truncate
        max_length: Maximum length of the returned string including suffix
        suffix: Suffix to add if text is truncated
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0, 
          exceptions: tuple = (Exception,)):
    """
    Retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier (e.g., 2 means delay doubles each retry)
        exceptions: Tuple of exceptions to catch and retry
        
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            attempts = 0
            current_delay = delay
            
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempts += 1
                    if attempts == max_attempts:
                        raise
                    
                    # Sleep with exponential backoff
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            return func(*args, **kwargs)  # Final attempt
        
        return wrapper
    
    return decorator


def is_valid_email(email: str) -> bool:
    """
    Check if an email address is valid using a simple regex.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if the email is valid, False otherwise
    """
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    return bool(email_pattern.match(email)) 