# mananeras

Scripts that pull **written transcripts** of Mexico’s presidential morning press conferences (“mañaneras”) from the official site [gob.mx](https://www.gob.mx), normalize them into plain text under `articulos/`, and (in the default workflow) publish updates to the Kaggle dataset [Conferencias Mañaneras](https://www.kaggle.com/datasets/ioexception/mananeras).

## Requirements

- **Python** 3.8+
- **[Poetry](https://python-poetry.org/)** for dependencies
- **[Playwright](https://playwright.dev/python/)** Chromium (the archive listing is loaded in a browser after a bot challenge)

## Run locally

From the repository root:

```bash
poetry install
poetry run playwright install chromium
```

End-to-end pipeline (scrape listing → download HTML → extract text → zip → **upload to Kaggle**):

```bash
export KAGGLE_USERNAME=your_kaggle_username
export KAGGLE_KEY=your_kaggle_api_key

poetry run python -m mananeras
```

The Kaggle API credentials are only needed for the final upload step. Without them, the earlier steps would still need code changes to skip `api.dataset_create_version` in `mananeras/__main__.py`.

Outputs include `urls.txt`, `raw/` (HTML), `articulos/` (`.txt` by date), and `data/articulos.zip` when the run completes.
