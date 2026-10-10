from pathlib import Path
from typing import Dict, List
from unittest.mock import MagicMock, call, patch

from playwright.sync_api import TimeoutError as PlaywrightTimeout

from mananeras.dataset.download_urls import (
    _create_browser_context,
    _fetch_listing_page,
    _wait_past_challenge,
    article_slug,
    collect_new_urls,
    read_known_slugs,
    url_slug,
)


def _pages(pages: Dict[int, List[str]]):
    def fetch_links(page_num: int) -> List[str]:
        return pages.get(page_num, [])

    return fetch_links


def test_read_known_slugs_missing_directory(tmp_path: Path):
    assert read_known_slugs(tmp_path / "data") == set()


def test_read_known_slugs_from_nested_articles(tmp_path: Path):
    for name in ["2019/mayo/02--conferencia-b.txt", "2026/octubre/09--conferencia-a--con-guiones.txt"]:
        article = tmp_path / name
        article.parent.mkdir(parents=True, exist_ok=True)
        article.write_text("")
    (tmp_path / "dataset-metadata.json").write_text("{}")

    assert read_known_slugs(tmp_path) == {"conferencia-b", "conferencia-a--con-guiones"}


def test_slugs_of_url_and_article_agree():
    url = "https://www.gob.mx/presidencia/es/articulos/version-estenografica-del-09-de-octubre-de-2026"
    article = Path("data/2026/octubre/09--version-estenografica-del-09-de-octubre-de-2026.txt")

    assert url_slug(url) == article_slug(article) == "version-estenografica-del-09-de-octubre-de-2026"


def test_collect_new_urls_stops_at_page_without_news():
    fetch = _pages({1: ["/x/d", "/x/c"], 2: ["/x/b", "/x/a"], 3: ["/x/z"]})

    assert collect_new_urls(["b", "a"], 1, fetch) == ["/x/d", "/x/c"]


def test_collect_new_urls_stops_when_listing_runs_out():
    fetch = _pages({1: ["c", "b"], 2: ["a"]})

    assert collect_new_urls([], 1, fetch) == ["c", "b", "a"]


def test_collect_new_urls_recovers_a_gap():
    """A URL missed by an earlier failed run is picked up even though newer ones are known."""
    fetch = _pages({1: ["/x/c", "/x/b", "/x/a"], 2: []})

    assert collect_new_urls(["c", "a"], 1, fetch) == ["/x/b"]


def test_collect_new_urls_ignores_duplicates_across_pages():
    fetch = _pages({1: ["b"], 2: ["b", "a"], 3: []})

    assert collect_new_urls([], 1, fetch) == ["b", "a"]


def test_collect_new_urls_returns_nothing_when_up_to_date():
    fetch = _pages({1: ["/x/b", "/x/a"]})

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
