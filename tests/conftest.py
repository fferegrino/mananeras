import pytest
from _pytest.config import Config
from pathlib import Path

@pytest.fixture
def sample_docs_path(pytestconfig: Config) -> Path:
    return Path(pytestconfig.rootdir / "tests"/ "sample_docs")
