import os
import sys
import pytest
from fastapi.testclient import TestClient

# Add echolink_api to sys.path so we can import main and database directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app

@pytest.fixture
def client():
    """Fixture providing a TestClient for FastAPI tests."""
    with TestClient(app) as test_client:
        yield test_client
