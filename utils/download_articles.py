from pathlib import Path
from urllib.request import urlretrieve


def download(url_list, download_folder):
    url_list = Path(url_list)
    download_folder = Path(download_folder)
    download_folder.mkdir(parents=True, exist_ok=True)
    downloaded_urls = download_folder / "fetched.txt"

    downloaded_set = set()
    old_downloaded = []

    if downloaded_urls.exists():
        with open(downloaded_urls) as reader:
            for line in reader:
                aux = line.strip()
                downloaded_set.add(aux)
                old_downloaded.append(aux)

    new_downloaded = []
    with open(url_list) as reader:
        for line in reader:
            url = line.strip()
            if url in downloaded_set:
                break
            new_downloaded.append(url)
            _ , _, name = url.rpartition("/")
            urlretrieve(url, download_folder / f"{name}.html")

    all_urls = new_downloaded + old_downloaded

    with open(downloaded_urls, "w") as writable:
        for url in all_urls:
            writable.write(url + "\n")




