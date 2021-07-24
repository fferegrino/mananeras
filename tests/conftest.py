from pathlib import Path

import pytest
from _pytest.config import Config


@pytest.fixture
def sample_docs_path(pytestconfig: Config) -> Path:
    return Path(pytestconfig.rootdir / "tests" / "sample_docs")
