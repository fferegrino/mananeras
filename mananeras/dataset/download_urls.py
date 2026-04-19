import re
from pathlib import Path
from typing import Dict, List

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

base_url = "https://www.gob.mx"
articles_url = base_url + "/presidencia/es/archivo/articulos?page="

_ua = UserAgent(
    fallback=(
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
)

raw_path = Path("raw")
raw_path.mkdir(exist_ok=True, parents=True)


def _sec_ch_ua_platform(user_agent: str) -> str:
    if "Windows" in user_agent:
        return '"Windows"'
    if "Macintosh" in user_agent or "Mac OS X" in user_agent:
        return '"macOS"'
    return '"Linux"'


def _request_headers() -> Dict[str, str]:
    user_agent = _ua.chrome
    chrome_m = re.search(r"Chrome/(\d+)\.", user_agent)
    version = chrome_m.group(1) if chrome_m else "131"
    sec_ch_ua = (
        f'"Chromium";v="{version}", "Google Chrome";v="{version}", "Not_A Brand";v="24"'
    )
    return {
        "User-Agent": user_agent,
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,image/apng,*/*;q=0.8,"
            "application/signed-exchange;v=b3;q=0.7"
        ),
        "Accept-Language": "es-MX,es;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "sec-ch-ua": sec_ch_ua,
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": _sec_ch_ua_platform(user_agent),
    }


def query(page_to_query):
    response = requests.get(articles_url + str(page_to_query), headers=_request_headers())
    breakpoint()
    data = [
        BeautifulSoup(d.strip()[21:-2].replace('\\"', '"').replace(r"\/", "/").replace("\\n", ""), "html5lib")
        for d in response.text.split("\n")
        if d.strip()[4:10] == "prensa"
    ]

    return data


def clean_url(url):
    qmark = url.find("?")
    if qmark != -1:
        true_link = url[:qmark]
    else:
        true_link = url
    return base_url + true_link


def get_anchors(documents):
    anchors = []
    for doc in documents:
        anchors.extend([clean_url(a["href"]) for a in doc.find_all("a")])
    return anchors


def get_new_urls(url_list, page) -> List[str]:
    page = page or 1
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

    print(f"Starting fetching from page {page}")

    new_urls = []
    stop_crawling = False
    while not stop_crawling:
        results = query(page)
        if not results:
            print("No more urls, no need to dataset anymore")
            break

        if page % 10 == 0:
            print(f"Querying page {page}")

        for link in get_anchors(results):
            if link == last_fetched:
                print("Found a previously crawled page, no need to dataset anymore")
                stop_crawling = True
                break
            new_urls.append(link)

        page += 1

    all_urls = new_urls + old_urls
    with open(url_list, "w") as writable:
        for url in all_urls:
            writable.write(url + "\n")

    return new_urls
