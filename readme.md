# mananeras

Scripts that pull **written transcripts** of Mexico’s presidential morning press conferences (“mañaneras”) from the official site [gob.mx](https://www.gob.mx), normalize them into plain text, and publish them as the dataset Conferencias Mañaneras on [Hugging Face](https://huggingface.co/datasets/feregrino/mananeras) and [Kaggle](https://www.kaggle.com/datasets/ioexception/mananeras).

## Requirements

- **Python** 3.10+
- **[Poetry](https://python-poetry.org/)** for dependencies
- **[Playwright](https://playwright.dev/python/)** Chromium (the archive listing is loaded in a browser after a bot challenge)

## Run locally

From the repository root:

```bash
poetry install
poetry run playwright install chromium
```

The transcripts are not kept in this repository. The scheduled workflow downloads the current dataset from Hugging Face into `data/` with [dataset-sync](https://github.com/fferegrino/dataset-sync), adds any new conferences, and uploads the result to Hugging Face and Kaggle. The files already in `data/` are the record of what has been fetched, so a conference that failed to download or parse is retried on the next run.

To run the scraper locally, first download the dataset into `data/` (without it, the scraper starts from scratch and fetches the whole archive):

```bash
pip install huggingface_hub
hf download feregrino/mananeras --repo-type dataset --local-dir data

poetry run python -m mananeras
```

New transcripts are written to `data/` as `YYYY/mes/DD--slug.txt`, and the downloaded HTML to `raw/`. Nothing is uploaded.

## Reading the transcripts

`mananeras.reader` parses the text files into `Mananera` objects:

```python
from mananeras.reader import todas

for conferencia in todas("data"):
    print(conferencia.fecha, conferencia.titulo)
```

## Seeding a new destination

The workflow can be run by hand with `source: kaggle` to read the dataset from Kaggle instead, for example to fill a new Hugging Face dataset. Publishing never deletes files and refuses to change an existing transcript.
