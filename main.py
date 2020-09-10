from utils.download_urls import download_urls
from utils.download_articles import download_articles
from utils.extract_dialogs import extract
from kaggle import api
import shutil


def main():
    download_urls("urls.txt", 1)
    download_articles("urls.txt", "raw")
    extract("raw", "articulos")
    shutil.make_archive('data/articulos', 'zip', "articulos")
    api.dataset_create_version("data", "Daily dataset update", dir_mode="zip", quiet=False)


if __name__ == "__main__":
    main()