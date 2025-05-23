"""
Configuration settings for the Multi-Agent Lead Processing System.

This file contains all the configuration settings for the application,
including AWS credentials, database settings, and application constants.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = os.path.join(BASE_DIR, '.env')

# Load the .env file if it exists
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"Loaded environment variables from {env_path}")
else:
    print(f"Warning: .env file not found at {env_path}")

# Application Information
APP_NAME = "Multi-Agent Lead Processing System"
APP_VERSION = "1.0.0"
LOG_LEVEL = "INFO"

# Path Configuration
CSV_IMPORT_DIRECTORY = os.path.join(BASE_DIR, "data", "import")

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "multiagent_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123")

# AWS S3 Configuration
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY", "AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY", "AWS_SECRET_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_BUCKET = os.getenv("AWS_BUCKET", "leadhoop-recordings")
AWS_FOLDER = os.getenv("AWS_FOLDER", "ieim/eluminus_merge_142")
PUBLISHER_ID = os.getenv("PUBLISHER_ID", "142")

# Assistable.AI Configuration
ASSISTABLE_API_KEY = os.getenv("ASSISTABLE_API_KEY", "ASSISTABLE_API_KEY")
ASSISTABLE_BASE_URL = os.getenv("ASSISTABLE_BASE_URL", "https://api.assistable.ai")
ASSISTABLE_API_URL = ASSISTABLE_BASE_URL

# LeadHoop Configuration
LEADHOOP_PORTAL_URL = os.getenv("LEADHOOP_PORTAL_URL", "https://ieim-portal")
LEADHOOP_USERNAME = os.getenv("LEADHOOP_USERNAME", "LEADHOOP_USERNAME")
LEADHOOP_PASSWORD = os.getenv("LEADHOOP_PASSWORD", "LEADHOOP_PASSWORD")

# Voice Agent Configuration
MAX_CONCURRENT_CALLS = 5
CALL_RETRY_ATTEMPTS = 3
CALL_TIMEOUT_SECONDS = 300
TCPA_COMPLIANCE_TEXT = "This call is being recorded for quality assurance purposes"

# Data Entry Agent Configuration
MAX_CONCURRENT_DATA_ENTRIES = 3
ENTRY_RETRY_ATTEMPTS = 3
ENTRY_TIMEOUT_SECONDS = 300 