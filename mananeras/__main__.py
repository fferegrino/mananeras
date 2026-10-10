import logging

import click

from mananeras.dataset.download_articles import download_articles
from mananeras.dataset.download_urls import crawl_new_urls, read_known_slugs, url_slug
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

    # data/ is the published dataset, fetched before the run and uploaded after it by dataset-sync.
    logger.info("downloading urls")
    new_urls = crawl_new_urls(read_known_slugs("data"), 1)
    logger.info("downloading articles")
    downloaded_urls = download_articles(new_urls, "raw")
    logger.info("processing articles")
    extracted = extract("raw", "data")
    # Nothing else to record: an article missing here is crawled again on the next run.
    failed = [url for url in downloaded_urls if url_slug(url) not in extracted]
    if failed:
        logger.warning("Could not extract %d of %d downloaded articles", len(failed), len(downloaded_urls))


if __name__ == "__main__":
    main()
