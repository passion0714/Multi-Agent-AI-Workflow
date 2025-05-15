"""
Database package for Voice AI Agent system.

This package serves as a namespace for the database models and functions.
It re-exports all models and functions from the main models module.
"""

# Ensure backward compatibility by re-exporting from the models module
from shared.database.models import * 