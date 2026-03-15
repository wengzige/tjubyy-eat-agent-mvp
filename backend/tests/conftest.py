import shutil
from pathlib import Path
from typing import Iterator
from uuid import uuid4

import pytest


TEST_TMP_ROOT = Path(__file__).resolve().parents[1] / "test-fixture-tmp"


@pytest.fixture
def tmp_path() -> Iterator[Path]:
    TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)
    path = TEST_TMP_ROOT / uuid4().hex
    path.mkdir()
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
