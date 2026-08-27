import logging
import shutil

import click
from kaggle import api

from mananeras.dataset.download_articles import download_articles
from mananeras.dataset.download_urls import crawl_new_urls, read_known_urls, record_urls
from mananeras.dataset.extract_dialogs import extract


def setup_logger():
    logger = logging.getLogger("mananeras")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
        logger.addHandler(handler)
    return logger


@click.command()
def main():
    logger = setup_logger()

    logger.info("downloading urls")
    known_urls = read_known_urls("urls.txt")
    new_urls = crawl_new_urls(known_urls, 1)
    logger.info("downloading articles")
    downloaded_urls = download_articles(new_urls, "raw")
    logger.info("processing articles")
    extract("raw", "articulos")
    # Only recorded once the articles are safely extracted, so that a failure part way
    # through is retried on the next run instead of being skipped forever.
    record_urls("urls.txt", downloaded_urls, known_urls)
    logger.info("compressing articles")
    shutil.make_archive("data/articulos", "zip", "./articulos")
    logger.info("creating new dataset version")
    api.dataset_create_version("data", "Daily dataset update", dir_mode="zip", quiet=False)


if __name__ == "__main__":
    main()
