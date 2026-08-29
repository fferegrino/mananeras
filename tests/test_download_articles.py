from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeout

from mananeras.dataset.download_articles import (
    _download_single_article,
    download_articles,
)

GOOD = "https://example.com/articulos/buena"
BAD = "https://example.com/articulos/mala"


@pytest.fixture
def fake_browser(monkeypatch):
    """Mock sync_playwright and browser context for download_articles."""
    failing = set()

    mock_playwright = MagicMock()
    mock_browser = MagicMock()
    mock_context = MagicMock()
    mock_page = MagicMock()

    mock_playwright.__enter__.return_value = mock_playwright
    mock_playwright.chromium.launch.return_value = mock_browser
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page

    def fake_goto(url, **kwargs):
        if url in failing:
            raise PlaywrightTimeout(f"Failed to fetch {url}")
        mock_page.title.return_value = "Article Title"
        mock_page.content.return_value = "<html><body><article>Content</article></body></html>"

    mock_page.goto.side_effect = fake_goto

    monkeypatch.setattr(
        "mananeras.dataset.download_articles.sync_playwright",
        lambda: mock_playwright,
    )
    return failing


def test_returns_downloaded_urls(tmp_path: Path, fake_browser):
    assert download_articles([GOOD], tmp_path) == [GOOD]
    assert (tmp_path / "buena.html").exists()


def test_failed_download_is_not_reported(tmp_path: Path, fake_browser):
    fake_browser.add(BAD)

    assert download_articles([BAD], tmp_path) == []


def test_failure_does_not_stop_the_remaining_urls(tmp_path: Path, fake_browser):
    fake_browser.add(BAD)

    assert download_articles([BAD, GOOD], tmp_path) == [GOOD]
    assert (tmp_path / "buena.html").exists()


@patch("time.sleep")
def test_partial_file_is_removed_on_failure(mock_sleep, tmp_path: Path):
    mock_page = MagicMock()
    mock_page.goto.return_value = None
    mock_page.title.return_value = "Challenge Validation"

    destination = tmp_path / "mala.html"
    result = _download_single_article(mock_page, BAD, destination, max_retries=2)

    assert not result
    assert not destination.exists()
    assert mock_page.goto.call_count == 2
    mock_sleep.assert_called_once_with(2)


def test_creates_the_download_folder(tmp_path: Path, fake_browser):
    destination = tmp_path / "raw"

    download_articles([GOOD], destination)

    assert destination.is_dir()


def test_empty_url_list_returns_empty(tmp_path: Path):
    assert download_articles([], tmp_path) == []
