import logging
import shutil

import click
from kaggle import api

from mananeras.dataset.download_articles import download_articles
from mananeras.dataset.download_urls import get_new_urls
from mananeras.dataset.extract_dialogs import extract


def setup_logger():
    logger = logging.getLogger("mananeras")
    logger.setLevel(logging.INFO)
    return logger


@click.command()
def main():
    logger = setup_logger()

    logger.info("downloading urls")
    new_urls = get_new_urls("urls.txt", 1)
    logger.info("downloading articles")
    download_articles(new_urls, "raw")
    logger.info("processing articles")
    extract("raw", "articulos")
    logger.info("compressing articles")
    shutil.make_archive("data/articulos", "zip", "./articulos")
    logger.info("creating new dataset version")
    api.dataset_create_version("data", "Daily dataset update", dir_mode="zip", quiet=False)


if __name__ == "__main__":
    main()
