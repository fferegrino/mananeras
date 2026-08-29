import logging
import time
from pathlib import Path
from typing import List

from playwright.sync_api import Page, sync_playwright

from mananeras.dataset.download_urls import (
    CHROMIUM_ARGS,
    _create_browser_context,
    _wait_past_challenge,
)

logger = logging.getLogger(__name__)


def _download_single_article(page: Page, url: str, destination: Path, max_retries: int = 3) -> bool:
    for attempt in range(1, max_retries + 1):
        try:
            logger.info("Downloading article %s (attempt %d/%d)", url, attempt, max_retries)
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            _wait_past_challenge(page, timeout_ms=45000)

            title = page.title()
            if "Challenge Validation" in title:
                raise ValueError("Encountered Challenge Validation")

            content = page.content()
            if not content or "<html" not in content.lower():
                raise ValueError("Empty or invalid HTML content")

            destination.write_text(content, encoding="utf-8")
            return True
        except Exception as exc:
            logger.warning(
                "Attempt %d/%d to download %s failed: %s",
                attempt,
                max_retries,
                url,
                exc,
            )
            destination.unlink(missing_ok=True)
            if attempt < max_retries:
                time.sleep(2 * attempt)
    return False


def download_articles(url_list: List[str], download_folder) -> List[str]:
    """Download each article, returning only the URLs that were stored successfully.

    A URL that fails here must not be recorded as fetched, otherwise it would be
    skipped forever on later runs.
    """
    download_folder = Path(download_folder)
    download_folder.mkdir(parents=True, exist_ok=True)

    if not url_list:
        return []

    downloaded = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=CHROMIUM_ARGS)
        try:
            context = _create_browser_context(browser)
            page = context.new_page()
            for url in url_list:
                _, _, name = url.rpartition("/")
                destination = download_folder / f"{name}.html"
                if _download_single_article(page, url, destination):
                    downloaded.append(url)
        finally:
            browser.close()

    if len(downloaded) != len(url_list):
        logger.warning("Downloaded %d of %d articles", len(downloaded), len(url_list))

    return downloaded
