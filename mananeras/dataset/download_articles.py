import logging
from pathlib import Path
from typing import List
from urllib.error import URLError
from urllib.request import urlretrieve

logger = logging.getLogger(__name__)


def download_articles(url_list: List[str], download_folder) -> List[str]:
    """Download each article, returning only the URLs that were stored successfully.

    A URL that fails here must not be recorded as fetched, otherwise it would be
    skipped forever on later runs.
    """
    download_folder = Path(download_folder)
    download_folder.mkdir(parents=True, exist_ok=True)

    downloaded = []
    for url in url_list:
        _, _, name = url.rpartition("/")
        destination = download_folder / f"{name}.html"
        try:
            urlretrieve(url, destination)
        except (URLError, OSError) as exc:
            logger.warning("Could not download %s: %s", url, exc)
            destination.unlink(missing_ok=True)
            continue
        downloaded.append(url)

    if len(downloaded) != len(url_list):
        logger.warning("Downloaded %d of %d articles", len(downloaded), len(url_list))

    return downloaded
