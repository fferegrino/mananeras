
import requests
from bs4 import BeautifulSoup
from pathlib import Path


base_url = "https://www.gob.mx"
articles_url = base_url + "/presidencia/es/archivo/articulos?page="
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
}
raw_path = Path("raw")
raw_path.mkdir(exist_ok=True, parents=True)


def query(page_to_query):
    response = requests.get(articles_url + str(page_to_query), headers=headers)
    data = [
        BeautifulSoup(
            d.strip()[21:-2].replace('\\\"', "\"").replace(r'\/', "/").replace('\\n', "")
            , "html5lib")
        for d in response.text.split('\n') if d.strip()[4:10] == 'prensa']

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

def download_urls(url_list, page):
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
            print("No more urls, no need to crawl anymore")
            break

        if page % 10 == 0:
            print(f"Querying page {page}")

        for link in get_anchors(results):
            if link == last_fetched:
                print("Found a previously crawled page, no need to crawl anymore")
                stop_crawling = True
                break
            new_urls.append(link)

        page += 1

    all_urls = new_urls + old_urls
    with open(url_list, "w") as writable:
        for url in all_urls:
            writable.write(url + "\n")
