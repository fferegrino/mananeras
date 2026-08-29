from pathlib import Path
from typing import Dict, List
from unittest.mock import MagicMock, call, patch

from playwright.sync_api import TimeoutError as PlaywrightTimeout

from mananeras.dataset.download_urls import (
    _create_browser_context,
    _fetch_listing_page,
    _wait_past_challenge,
    collect_new_urls,
    read_known_urls,
    record_urls,
)


def _pages(pages: Dict[int, List[str]]):
    def fetch_links(page_num: int) -> List[str]:
        return pages.get(page_num, [])

    return fetch_links


def test_read_known_urls_missing_file(tmp_path: Path):
    assert read_known_urls(tmp_path / "urls.txt") == []


def test_read_known_urls_skips_blank_lines(tmp_path: Path):
    url_list = tmp_path / "urls.txt"
    url_list.write_text("a\nb\n\n")

    assert read_known_urls(url_list) == ["a", "b"]


def test_record_urls_creates_file(tmp_path: Path):
    url_list = tmp_path / "urls.txt"

    record_urls(url_list, ["a"], [])

    assert url_list.read_text() == "a\n"


def test_record_urls_is_prepend_only(tmp_path: Path):
    """The old lines must survive byte for byte, in order, or git delta compression collapses."""
    url_list = tmp_path / "urls.txt"
    known = ["c", "b", "a"]
    record_urls(url_list, [], known)
    before = url_list.read_text()

    record_urls(url_list, ["e", "d"], known)

    after = url_list.read_text()
    assert after == "e\nd\n" + before
    assert after.splitlines() == ["e", "d", "c", "b", "a"]


def test_record_urls_round_trips(tmp_path: Path):
    url_list = tmp_path / "urls.txt"

    record_urls(url_list, ["b", "a"], [])

    assert read_known_urls(url_list) == ["b", "a"]


def test_collect_new_urls_stops_at_page_without_news():
    fetch = _pages({1: ["d", "c"], 2: ["b", "a"], 3: ["z"]})

    assert collect_new_urls(["b", "a"], 1, fetch) == ["d", "c"]


def test_collect_new_urls_stops_when_listing_runs_out():
    fetch = _pages({1: ["c", "b"], 2: ["a"]})

    assert collect_new_urls([], 1, fetch) == ["c", "b", "a"]


def test_collect_new_urls_recovers_a_gap():
    """A URL missed by an earlier failed run is picked up even though newer ones are known."""
    fetch = _pages({1: ["c", "b", "a"], 2: []})

    assert collect_new_urls(["c", "a"], 1, fetch) == ["b"]


def test_collect_new_urls_ignores_duplicates_across_pages():
    fetch = _pages({1: ["b"], 2: ["b", "a"], 3: []})

    assert collect_new_urls([], 1, fetch) == ["b", "a"]


def test_collect_new_urls_returns_nothing_when_up_to_date():
    fetch = _pages({1: ["b", "a"]})

    assert collect_new_urls(["b", "a"], 1, fetch) == []


def test_wait_past_challenge():
    mock_page = MagicMock()
    _wait_past_challenge(mock_page, timeout_ms=30000)
    mock_page.wait_for_function.assert_called_once_with(
        "() => document.title !== 'Challenge Validation'",
        timeout=30000,
    )


def test_create_browser_context():
    mock_browser = MagicMock()
    _create_browser_context(mock_browser)
    mock_browser.new_context.assert_called_once()
    context = mock_browser.new_context.return_value
    context.add_init_script.assert_called_once()


def test_fetch_listing_page_success():
    mock_page = MagicMock()
    mock_page.content.return_value = '<html><a href="/articulos/prensa-1">Prensa</a></html>'
    docs = _fetch_listing_page(mock_page, 1, max_retries=2)
    assert len(docs) == 1
    assert "prensa-1" in docs[0].decode()


@patch("time.sleep")
def test_fetch_listing_page_retry_success(mock_sleep):
    mock_page = MagicMock()
    mock_page.goto.side_effect = [PlaywrightTimeout("Timeout 1"), None]
    mock_page.content.return_value = '<html><a href="/articulos/prensa-1">Prensa</a></html>'

    docs = _fetch_listing_page(mock_page, 1, max_retries=2)

    assert len(docs) == 1
    assert mock_page.goto.call_count == 2
    mock_sleep.assert_called_once_with(2)


@patch("time.sleep")
def test_fetch_listing_page_all_retries_fail(mock_sleep):
    mock_page = MagicMock()
    mock_page.goto.side_effect = PlaywrightTimeout("Timeout exceeded")

    docs = _fetch_listing_page(mock_page, 1, max_retries=3)

    assert docs == []
    assert mock_page.goto.call_count == 3
    assert mock_sleep.call_args_list == [call(2), call(4)]
