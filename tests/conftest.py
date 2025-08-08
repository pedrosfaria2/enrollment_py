import os
import tempfile
from pathlib import Path

import pytest
from tinydb import TinyDB
from tinydb.storages import JSONStorage

TEST_DB_FILE = tempfile.mktemp(prefix="test_db_", suffix=".json")
os.environ["DB_FILE_PATH"] = TEST_DB_FILE

_DB = TinyDB(TEST_DB_FILE, storage=JSONStorage)


@pytest.fixture(scope="session")
def tmp_db():
    yield _DB
    _DB.close()
    Path(TEST_DB_FILE).unlink(missing_ok=True)
