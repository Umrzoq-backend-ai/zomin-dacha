import os
import tempfile
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.database import init_db, seed_initial_data

@pytest.fixture
def test_db_path():
    temp_dir = tempfile.mkdtemp()
    db_file = os.path.join(temp_dir, "test_zomin.db")
    settings.DATABASE_PATH = db_file
    init_db(db_file)
    seed_initial_data(db_file)
    yield db_file
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except OSError:
            pass

@pytest.fixture
def client(test_db_path):
    with TestClient(app) as test_client:
        yield test_client
