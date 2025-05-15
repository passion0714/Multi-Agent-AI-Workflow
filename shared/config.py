"""
Configuration module for the Voice AI Agent system.

This module loads configuration from environment variables and provides
a unified interface for accessing configuration values throughout the system.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def load_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables.
    
    Returns:
        Dictionary containing all configuration values.
    """
    config = {
        # Database Configuration
        'DATABASE_URL': os.getenv('DATABASE_URL', 'postgresql://postgres:123@localhost:5432/multiagent_db'),
        'DB_POOL_SIZE': os.getenv('DB_POOL_SIZE', '5'),
        'DB_MAX_OVERFLOW': os.getenv('DB_MAX_OVERFLOW', '10'),
        'DB_POOL_TIMEOUT': os.getenv('DB_POOL_TIMEOUT', '30'),
        'DB_POOL_RECYCLE': os.getenv('DB_POOL_RECYCLE', '1800'),
        
        # Voice API Configuration
        'VOICE_API_KEY': os.getenv('VOICE_API_KEY', ''),
        'VOICE_API_PROVIDER': os.getenv('VOICE_API_PROVIDER', 'twilio'),  # twilio, deepgram, etc.
        'VOICE_API_BASE_URL': os.getenv('VOICE_API_BASE_URL', ''),
        'TWILIO_ACCOUNT_SID': os.getenv('TWILIO_ACCOUNT_SID', ''),
        'TWILIO_AUTH_TOKEN': os.getenv('TWILIO_AUTH_TOKEN', ''),
        'TWILIO_PHONE_NUMBER': os.getenv('TWILIO_PHONE_NUMBER', ''),
        'DEEPGRAM_API_KEY': os.getenv('DEEPGRAM_API_KEY', ''),
        
        # Lead Hoop Configuration
        'LEAD_HOOP_URL': os.getenv('LEAD_HOOP_URL', 'https://leadhoop.com'),
        'LEAD_HOOP_USERNAME': os.getenv('LEAD_HOOP_USERNAME', ''),
        'LEAD_HOOP_PASSWORD': os.getenv('LEAD_HOOP_PASSWORD', ''),
        'LEAD_HOOP_TIMEOUT': os.getenv('LEAD_HOOP_TIMEOUT', '60'),
        'LEAD_HOOP_RETRY_ATTEMPTS': os.getenv('LEAD_HOOP_RETRY_ATTEMPTS', '3'),
        
        # API Configuration
        'API_HOST': os.getenv('API_HOST', '0.0.0.0'),
        'API_PORT': os.getenv('API_PORT', '8000'),
        'API_KEY': os.getenv('API_KEY', 'development_key'),
        
        # Agent Configuration
        'VOICE_AGENT_POLLING_INTERVAL': os.getenv('VOICE_AGENT_POLLING_INTERVAL', '30'),
        'DATA_ENTRY_AGENT_POLLING_INTERVAL': os.getenv('DATA_ENTRY_AGENT_POLLING_INTERVAL', '60'),
        'MAX_CONCURRENT_CALLS': os.getenv('MAX_CONCURRENT_CALLS', '3'),
        'MAX_CONCURRENT_ENTRIES': os.getenv('MAX_CONCURRENT_ENTRIES', '1'),
        'AGENT_BROWSER_HEADLESS': os.getenv('AGENT_BROWSER_HEADLESS', 'true'),
        'AGENT_RETRY_COUNT': os.getenv('AGENT_RETRY_COUNT', '3'),
        
        # Logging Configuration
        'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
        'ENVIRONMENT': os.getenv('ENVIRONMENT', 'development'),
    }
    
    return config


def get_lead_hoop_config() -> Dict[str, Any]:
    """
    Get Lead Hoop specific configuration.
    
    Returns:
        Dictionary containing Lead Hoop configuration values.
        Note: If using a direct portal URL, username and password may be empty.
    """
    config = load_config()
    
    # Using a dictionary so we don't include empty strings for username/password if they're not set
    lead_hoop_config = {
        'url': config['LEAD_HOOP_URL'],
        'timeout': int(config['LEAD_HOOP_TIMEOUT']),
        'retry_attempts': int(config['LEAD_HOOP_RETRY_ATTEMPTS']),
    }
    
    # Only add username and password if they are set
    if config['LEAD_HOOP_USERNAME']:
        lead_hoop_config['username'] = config['LEAD_HOOP_USERNAME']
    
    if config['LEAD_HOOP_PASSWORD']:
        lead_hoop_config['password'] = config['LEAD_HOOP_PASSWORD']
    
    # Check if this is a direct portal URL by looking for 'consumer' in the URL
    # This is specific to the client's LeadHoop setup
    if 'consumer' in config['LEAD_HOOP_URL'].lower():
        lead_hoop_config['is_direct_portal'] = True
    else:
        lead_hoop_config['is_direct_portal'] = False
    
    return lead_hoop_config


def get_voice_api_config() -> Dict[str, Any]:
    """
    Get Voice API specific configuration based on the provider.
    
    Returns:
        Dictionary containing Voice API configuration values for the selected provider.
    """
    config = load_config()
    provider = config['VOICE_API_PROVIDER'].lower()
    
    base_config = {
        'provider': provider,
        'api_key': config['VOICE_API_KEY'],
        'base_url': config['VOICE_API_BASE_URL'],
    }
    
    if provider == 'twilio':
        return {
            **base_config,
            'account_sid': config['TWILIO_ACCOUNT_SID'],
            'auth_token': config['TWILIO_AUTH_TOKEN'],
            'phone_number': config['TWILIO_PHONE_NUMBER'],
        }
    elif provider == 'deepgram':
        return {
            **base_config,
            'deepgram_api_key': config['DEEPGRAM_API_KEY'],
        }
    else:
        return base_config


def get_db_config() -> Dict[str, Any]:
    """
    Get database specific configuration.
    
    Returns:
        Dictionary containing database configuration values.
    """
    config = load_config()
    return {
        'url': config['DATABASE_URL'],
        'pool_size': int(config['DB_POOL_SIZE']),
        'max_overflow': int(config['DB_MAX_OVERFLOW']),
        'pool_timeout': int(config['DB_POOL_TIMEOUT']),
        'pool_recycle': int(config['DB_POOL_RECYCLE']),
    }


def get_api_config() -> Dict[str, Any]:
    """
    Get API server specific configuration.
    
    Returns:
        Dictionary containing API configuration values.
    """
    config = load_config()
    return {
        'host': config['API_HOST'],
        'port': int(config['API_PORT']),
        'api_key': config['API_KEY'],
    }


# Initialize common configuration variables
config = load_config()
LOG_LEVEL = config['LOG_LEVEL']
ENVIRONMENT = config['ENVIRONMENT']
DATABASE_URL = config['DATABASE_URL']
API_HOST = config['API_HOST']
API_PORT = int(config['API_PORT'])
LEAD_HOOP_URL = config['LEAD_HOOP_URL']

# Clean any potential comments from the values before converting to int
try:
    VOICE_AGENT_POLLING_INTERVAL = int(config['VOICE_AGENT_POLLING_INTERVAL'].split('#')[0].strip())
except (ValueError, AttributeError):
    VOICE_AGENT_POLLING_INTERVAL = 5  # Default value

try:
    DATA_ENTRY_AGENT_POLLING_INTERVAL = int(config['DATA_ENTRY_AGENT_POLLING_INTERVAL'].split('#')[0].strip())
except (ValueError, AttributeError):
    DATA_ENTRY_AGENT_POLLING_INTERVAL = 5  # Default value

try:
    MAX_CONCURRENT_CALLS = int(config['MAX_CONCURRENT_CALLS'].split('#')[0].strip())
except (ValueError, AttributeError):
    MAX_CONCURRENT_CALLS = 5  # Default value

try:
    MAX_CONCURRENT_ENTRIES = int(config['MAX_CONCURRENT_ENTRIES'].split('#')[0].strip())
except (ValueError, AttributeError):
    MAX_CONCURRENT_ENTRIES = 3  # Default value

# Handle boolean configuration
HEADLESS_BROWSER_VALUE = config['AGENT_BROWSER_HEADLESS']
if isinstance(HEADLESS_BROWSER_VALUE, str):
    HEADLESS_BROWSER_VALUE = HEADLESS_BROWSER_VALUE.split('#')[0].strip()
HEADLESS_BROWSER = HEADLESS_BROWSER_VALUE.lower() == 'true' if isinstance(HEADLESS_BROWSER_VALUE, str) else bool(HEADLESS_BROWSER_VALUE) 