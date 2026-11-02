import os
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

TEST_DSN = os.getenv("TEST_DATABASE_URL", "postgresql:///agos_test")

os.environ["DATABASE_URL"] = TEST_DSN
os.environ["AGOS_DATABASE_URL"] = TEST_DSN
os.environ["AGOS_ALLOW_DEV_USER"] = "1"
os.environ["AGOS_INTERNAL_SECRET"] = "test-internal-secret-0123456789abcdef"

from db.connection import get_pool
from db.init import init_db

@pytest.fixture(scope="session", autouse=True)
def _database():
    try:
        init_db(TEST_DSN)
    except Exception as exc:
        pytest.skip(f"Postgres test database unavailable: {exc}")
    yield
    get_pool().close()

@pytest.fixture(autouse=True)
def _clean(_database):
    with get_pool().connection() as conn:
        conn.execute(
            """
            TRUNCATE image_humanizations, images, sessions, users
            RESTART IDENTITY CASCADE
            """
        )
        conn.commit()
    yield
