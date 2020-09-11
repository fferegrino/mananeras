from utils.download_urls import download_urls
from utils.download_articles import download_articles
from utils.extract_dialogs import extract
from kaggle import api
import shutil
import logging
import click

def setup_logger(log_file):
    logger = logging.getLogger("mananeras")

    # Create handlers
    f_handler = logging.FileHandler(log_file)
    logger.setLevel(logging.INFO)

    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    f_handler.setFormatter(f_format)

    # Add handlers to the logger
    logger.addHandler(f_handler)

    return logger 

@click.command()
@click.argument("log_file", type=click.Path(dir_okay=False))
def main(log_file):
    logger = setup_logger(log_file)

    logger.info("downloading urls")
    download_urls("urls.txt", 1)
    logger.info("downloading articles")
    download_articles("urls.txt", "raw")
    extract("raw", "articulos")
    logger.info("compressing articles")
    shutil.make_archive('data/articulos', 'zip', "articulos")
    logger.info("creating new dataset version")
    api.dataset_create_version("data", "Daily dataset update", dir_mode="zip", quiet=False)


if __name__ == "__main__":
    main()