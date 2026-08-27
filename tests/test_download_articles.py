from pathlib import Path
from urllib.error import HTTPError

import pytest

from mananeras.dataset import download_articles as module
from mananeras.dataset.download_articles import download_articles

GOOD = "https://example.com/articulos/buena"
BAD = "https://example.com/articulos/mala"


@pytest.fixture
def fake_urlretrieve(monkeypatch):
    """Write a stub file for every URL except the ones marked as failing."""
    failing = set()

    def _urlretrieve(url, destination):
        if url in failing:
            raise HTTPError(url, 404, "Not Found", {}, None)
        Path(destination).write_text("<html></html>")

    monkeypatch.setattr(module, "urlretrieve", _urlretrieve)
    return failing


def test_returns_downloaded_urls(tmp_path: Path, fake_urlretrieve):
    assert download_articles([GOOD], tmp_path) == [GOOD]
    assert (tmp_path / "buena.html").exists()


def test_failed_download_is_not_reported(tmp_path: Path, fake_urlretrieve):
    fake_urlretrieve.add(BAD)

    assert download_articles([BAD], tmp_path) == []


def test_failure_does_not_stop_the_remaining_urls(tmp_path: Path, fake_urlretrieve):
    fake_urlretrieve.add(BAD)

    assert download_articles([BAD, GOOD], tmp_path) == [GOOD]
    assert (tmp_path / "buena.html").exists()


def test_partial_file_is_removed_on_failure(tmp_path: Path, monkeypatch):
    def _urlretrieve(url, destination):
        Path(destination).write_text("truncado")
        raise HTTPError(url, 500, "Server Error", {}, None)

    monkeypatch.setattr(module, "urlretrieve", _urlretrieve)

    assert download_articles([BAD], tmp_path) == []
    assert not (tmp_path / "mala.html").exists()


def test_creates_the_download_folder(tmp_path: Path, fake_urlretrieve):
    destination = tmp_path / "raw"

    download_articles([GOOD], destination)

    assert destination.is_dir()
