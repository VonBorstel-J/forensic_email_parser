# src/tests/conftest.py

import sys
import os

# Get the absolute path to the project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Define the src directory path
SRC_PATH = os.path.join(PROJECT_ROOT, 'src')

# Add src to sys.path if it's not already present
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)
