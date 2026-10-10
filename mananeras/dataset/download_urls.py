import logging
import time
from pathlib import Path
from typing import Callable, Iterable, List, Set

from bs4 import BeautifulSoup
from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeout,
    sync_playwright,
)

logger = logging.getLogger(__name__)

base_url = "https://www.gob.mx"
articles_url = base_url + "/presidencia/es/archivo/articulos?page="

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)

CHROMIUM_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-infobars",
    "--window-position=0,0",
    "--ignore-certificate-errors",
    "--ignore-certificate-errors-spki-list",
]

STEALTH_JS = """
// Pass the Webdriver Test.
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined,
});

// Pass the Plugins Length Test.
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5],
});

// Pass the Languages Test.
Object.defineProperty(navigator, 'languages', {
    get: () => ['es-MX', 'es', 'en-US', 'en'],
});

// Pass the Chrome Test.
window.chrome = {
    runtime: {},
};
"""


def _create_browser_context(browser: Browser) -> BrowserContext:
    context = browser.new_context(
        user_agent=DEFAULT_USER_AGENT,
        locale="es-MX",
        timezone_id="America/Mexico_City",
        viewport={"width": 1920, "height": 1080},
        extra_http_headers={
            "Accept-Language": "es-MX,es;q=0.9,en-US;q=0.8,en;q=0.7",
            "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
        },
    )
    context.add_init_script(STEALTH_JS)
    return context


def _wait_past_challenge(page: Page, timeout_ms: int = 45000) -> None:
    page.wait_for_function(
        "() => document.title !== 'Challenge Validation'",
        timeout=timeout_ms,
    )


def _fetch_listing_page(page: Page, page_num: int, max_retries: int = 3) -> List:
    url = articles_url + str(page_num)
    for attempt in range(1, max_retries + 1):
        try:
            logger.info("Fetching listing page %d (attempt %d/%d)", page_num, attempt, max_retries)
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            _wait_past_challenge(page, timeout_ms=45000)
            try:
                page.wait_for_selector('a[href*="/articulos/"][href*="prensa"]', timeout=30000)
            except PlaywrightTimeout:
                pass
            return [BeautifulSoup(page.content(), "html5lib")]
        except Exception as exc:
            logger.warning(
                "Attempt %d/%d to fetch page %d failed: %s",
                attempt,
                max_retries,
                page_num,
                exc,
            )
            if attempt < max_retries:
                time.sleep(2 * attempt)
            else:
                logger.error("Failed to fetch listing page %d after %d attempts", page_num, max_retries)
                return []
    return []


def query(page_to_query: int) -> List:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=CHROMIUM_ARGS)
        try:
            context = _create_browser_context(browser)
            pw = context.new_page()
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


def url_slug(url: str) -> str:
    return url.rpartition("/")[2]


def article_slug(article: Path) -> str:
    """The URL slug an extracted article was saved under, from its ``DD--slug.txt`` name."""
    return article.name.partition("--")[2][: -len(".txt")]


def read_known_slugs(articles_path) -> Set[str]:
    """The slugs of every article already extracted.

    The article tree is the record of what has been fetched: every URL is
    ``.../articulos/<slug>``, and an article is only written once it has been extracted,
    so a URL that failed to download or parse is retried on the next run.
    """
    known = {article_slug(article) for article in Path(articles_path).glob("**/*.txt")}
    logger.info("Found %d known articles", len(known))
    return known


def collect_new_urls(known_slugs: Iterable[str], page_num: int, fetch_links: Callable[[int], List[str]]) -> List[str]:
    """Walk the listing pages, newest first, collecting URLs whose slug is not already known.

    Crawling stops once a whole page holds nothing new. Scanning the complete page,
    instead of stopping at the first familiar URL, lets a gap left by an earlier failure
    be picked up on a later run.
    """
    known = set(known_slugs)
    seen = set()
    new_urls: List[str] = []

    while True:
        links = fetch_links(page_num)
        if not links:
            logger.info("No more urls, nothing left to crawl")
            break

        unknown = [link for link in links if url_slug(link) not in known and link not in seen]
        if not unknown:
            logger.info("Page %d holds nothing new, stopping", page_num)
            break

        seen.update(unknown)
        new_urls.extend(unknown)
        logger.info("Found %d new urls on page %d", len(unknown), page_num)
        page_num += 1

    return new_urls


def crawl_new_urls(known_slugs: Iterable[str], page: int = 1) -> List[str]:
    """Crawl the listing for URLs whose slug is missing from ``known_slugs``."""
    page_num = page or 1
    logger.info("Starting fetching from page %d", page_num)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=CHROMIUM_ARGS)
        try:
            context = _create_browser_context(browser)
            pw = context.new_page()

            def fetch_links(number: int) -> List[str]:
                return get_anchors(_fetch_listing_page(pw, number))

            return collect_new_urls(known_slugs, page_num, fetch_links)
        finally:
            browser.close()
