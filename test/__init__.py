"""
Unit tests for the Iron Condor Finder application.

These tests validate the functionality of the application components
using mock data, allowing testing without requiring actual API access.
"""

import os
import sys

# Add the parent directory to the Python path for all tests
# This makes importing from src/ work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) 