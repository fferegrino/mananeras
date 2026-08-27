import logging
from pathlib import Path
from typing import Callable, Iterable, List

from bs4 import BeautifulSoup
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout, sync_playwright

logger = logging.getLogger(__name__)

base_url = "https://www.gob.mx"
articles_url = base_url + "/presidencia/es/archivo/articulos?page="


def _wait_past_challenge(page: Page) -> None:
    page.wait_for_function(
        "() => document.title !== 'Challenge Validation'",
        timeout=120000,
    )


def _fetch_listing_page(page: Page, page_num: int) -> List:
    url = articles_url + str(page_num)
    page.goto(url, wait_until="domcontentloaded", timeout=120000)
    _wait_past_challenge(page)
    try:
        page.wait_for_selector('a[href*="/articulos/"][href*="prensa"]', timeout=90000)
    except PlaywrightTimeout:
        pass
    return [BeautifulSoup(page.content(), "html5lib")]


def query(page_to_query: int) -> List:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            pw = browser.new_page(locale="es-MX")
            return _fetch_listing_page(pw, page_to_query)
        finally:
            browser.close()


def clean_url(url):
    qmark = url.find("?")
    if qmark != -1:
        true_link = url[:qmark]
    else:
        true_link = url
    if true_link.startswith("http"):
        return true_link
    return base_url + true_link


def get_anchors(documents):
    anchors = []
    for doc in documents:
        for a in doc.find_all("a", href=True):
            href = a["href"]
            if "prensa" not in href or "/articulos/" not in href:
                continue
            anchors.append(clean_url(href))
    return anchors


def read_known_urls(url_list) -> List[str]:
    """Read the recorded URLs, newest first. Returns an empty list if there is no record yet."""
    url_list = Path(url_list)
    if not url_list.exists():
        logger.info("No previous urls found, starting from scratch")
        return []

    with open(url_list) as readable:
        known_urls = [line.strip() for line in readable if line.strip()]

    logger.info("Read %d known urls", len(known_urls))
    return known_urls


def record_urls(url_list, new_urls: Iterable[str], known_urls: Iterable[str]) -> None:
    """Prepend the newly fetched URLs to the record.

    This file must stay strictly prepend-only. Git delta-compresses each daily rewrite
    into roughly a kilobyte only because every existing line keeps its exact order and
    bytes. Sorting, deduplicating or otherwise reordering the record would turn every
    revision into a full snapshot, costing hundreds of kilobytes per day.
    """
    url_list = Path(url_list)
    url_list.parent.mkdir(exist_ok=True, parents=True)

    with open(url_list, "w") as writable:
        for url in list(new_urls) + list(known_urls):
            writable.write(url + "\n")


def collect_new_urls(known_urls: Iterable[str], page_num: int, fetch_links: Callable[[int], List[str]]) -> List[str]:
    """Walk the listing pages, newest first, collecting URLs that are not already known.

    Crawling stops once a whole page holds nothing new. Scanning the complete page,
    instead of stopping at the first familiar URL, lets a gap left by an earlier failure
    be picked up on a later run.
    """
    known = set(known_urls)
    seen = set()
    new_urls: List[str] = []

    while True:
        links = fetch_links(page_num)
        if not links:
            logger.info("No more urls, nothing left to crawl")
            break

        unknown = [link for link in links if link not in known and link not in seen]
        if not unknown:
            logger.info("Page %d holds nothing new, stopping", page_num)
            break

        seen.update(unknown)
        new_urls.extend(unknown)
        logger.info("Found %d new urls on page %d", len(unknown), page_num)
        page_num += 1

    return new_urls


def crawl_new_urls(known_urls: Iterable[str], page: int = 1) -> List[str]:
    """Crawl the listing for URLs missing from ``known_urls``, without recording anything."""
    page_num = page or 1
    logger.info("Starting fetching from page %d", page_num)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            pw = browser.new_page(locale="es-MX")

            def fetch_links(number: int) -> List[str]:
                return get_anchors(_fetch_listing_page(pw, number))

            return collect_new_urls(known_urls, page_num, fetch_links)
        finally:
            browser.close()
