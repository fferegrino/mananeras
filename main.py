from utils.download_urls import download_urls
from utils.download_articles import download_articles
from utils.extract_dialogs import extract


def main():
    download_urls("urls.txt", 1)
    download_articles("urls.txt", "raw")
    extract("raw", "articulos")


if __name__ == "__main__":
    main()