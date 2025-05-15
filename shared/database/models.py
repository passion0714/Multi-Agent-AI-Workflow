"""
Forwarding module for database models.

This module re-exports all models and functions from the main database/models.py
file to ensure backward compatibility with code that imports from shared.database.models.
"""

import sys
import importlib.util
from pathlib import Path

# Get the absolute path to the main models.py file
project_root = Path(__file__).parent.parent.parent
main_models_path = project_root / "database" / "models.py"

# Import the main models module
if not main_models_path.exists():
    raise ImportError(f"Main models file not found at {main_models_path}")

# Add project root to sys.path if not already there
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import everything from the main models module
from database.models import *

# For debugging purposes
print(f"Imported models from {main_models_path}", file=sys.stderr) 