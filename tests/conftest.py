"""
Pytest configuration and fixtures.
Ensures database tables are initialized before tests run.
"""

import pytest
from backend.database.connection import init_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Ensure database schema is created for test sessions."""
    init_db()
    yield

