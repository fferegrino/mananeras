from pathlib import Path
from typing import List

from bs4 import BeautifulSoup
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout, sync_playwright

base_url = "https://www.gob.mx"
articles_url = base_url + "/presidencia/es/archivo/articulos?page="

raw_path = Path("raw")
raw_path.mkdir(exist_ok=True, parents=True)


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


def get_new_urls(url_list, page) -> List[str]:
    page_num = page or 1
    url_list = Path(url_list)
    url_list.parent.mkdir(exist_ok=True, parents=True)
    last_fetched = None
    old_urls = []
    if url_list.exists():
        with open(url_list) as readable:
            for old_url in readable:
                old_urls.append(old_url.strip())
        last_fetched = old_urls[0]
        print(f"Last url found {last_fetched}")
    else:
        print("No previous urls found, starting from scratch")

    print(f"Starting fetching from page {page_num}")

    new_urls = []
    stop_crawling = False

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            pw = browser.new_page(locale="es-MX")
            while not stop_crawling:
                results = _fetch_listing_page(pw, page_num)
                links = get_anchors(results)
                if not links:
                    print("No more urls, no need to dataset anymore")
                    break

                if page_num % 10 == 0:
                    print(f"Querying page {page_num}")

                for link in links:
                    if link == last_fetched:
                        print("Found a previously crawled page, no need to dataset anymore")
                        stop_crawling = True
                        break
                    new_urls.append(link)

                page_num += 1
        finally:
            browser.close()

    all_urls = new_urls + old_urls
    with open(url_list, "w") as writable:
        for url in all_urls:
            writable.write(url + "\n")

    return new_urls
