from typing import List
from pathlib import Path
from urllib.request import urlretrieve


def download_articles(url_list: List[str], download_folder):
    download_folder = Path(download_folder)
    download_folder.mkdir(parents=True, exist_ok=True)

    for url in url_list:
        _, _, name = url.rpartition("/")
        urlretrieve(url, download_folder / f"{name}.html")
