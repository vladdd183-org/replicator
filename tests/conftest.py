"""Pytest configuration and shared fixtures.

Provides test database setup and common fixtures.
"""

import pytest
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Set test environment
os.environ["APP_ENV"] = "development"
os.environ["APP_DEBUG"] = "true"


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Setup test database before tests and cleanup after.
    
    Uses SQLite in-memory or separate test file.
    """
    # Use separate test database
    os.environ["DB_URL"] = "sqlite:///data/test.db"
    
    yield
    
    # Cleanup: remove test database file
    test_db_path = "data/test.db"
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except Exception:
            pass  # Ignore cleanup errors



