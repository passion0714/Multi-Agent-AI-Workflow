"""
Configuration settings for the Multi-Agent Lead Processing System.

This file contains all the configuration settings for the application,
including AWS credentials, database settings, and application constants.
"""
import os
from pathlib import Path

# Application Information
APP_NAME = "Multi-Agent Lead Processing System"
APP_VERSION = "1.0.0"
LOG_LEVEL = "INFO"

# Path Configuration
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CSV_IMPORT_DIRECTORY = os.path.join(BASE_DIR, "data", "import")

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "")
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# AWS S3 Configuration
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY", "")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY", "")
AWS_REGION = os.getenv("AWS_REGION", "")
AWS_BUCKET = os.getenv("AWS_BUCKET", "")
AWS_FOLDER = os.getenv("AWS_FOLDER", "")
PUBLISHER_ID = os.getenv("PUBLISHER_ID", "")

# Assistable.AI Configuration
ASSISTABLE_API_KEY = os.getenv("ASSISTABLE_API_KEY", "")
ASSISTABLE_BASE_URL = os.getenv("ASSISTABLE_BASE_URL", "")
ASSISTABLE_API_URL = ASSISTABLE_BASE_URL

# LeadHoop Configuration
LEADHOOP_PORTAL_URL = os.getenv("LEADHOOP_PORTAL_URL", "https://ieim-portal.leadhoop.com/consumer/new/aSuRzy0E8XWWKeLJngoDiQ")
LEADHOOP_USERNAME = os.getenv("LEADHOOP_USERNAME", "")
LEADHOOP_PASSWORD = os.getenv("LEADHOOP_PASSWORD", "")

# Voice Agent Configuration
MAX_CONCURRENT_CALLS = 5
CALL_RETRY_ATTEMPTS = 3
CALL_TIMEOUT_SECONDS = 300
TCPA_COMPLIANCE_TEXT = "This call is being recorded for quality assurance purposes"

# Data Entry Agent Configuration
MAX_CONCURRENT_DATA_ENTRIES = 3
ENTRY_RETRY_ATTEMPTS = 3
ENTRY_TIMEOUT_SECONDS = 300 