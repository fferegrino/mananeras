import logging
import re
from pathlib import Path
from typing import Dict, Tuple

from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

date_format = re.compile(
    r"(?P<day>[0-9]{1,2})(?:-(?:de-)?|\s*(?:de\s+)?|\s+)"
    r"(?P<month>[a-záéíóúñ]+)"
    r"(?:-(?:de-|-del-)?|\s*(?:de|del|,)\s*|\s+)"
    r"(?P<year>[0-9]{4})",
    re.IGNORECASE,
)


def _parse_date(date: str) -> Dict[str, str]:
    """Split a publication date such as '2 de junio de 2021' into its parts"""
    match = date_format.search(date)
    if not match:
        raise ValueError(f"Unrecognized publication date: {date!r}")
    date_info = match.groupdict()
    # Output paths are built from these values, so keep them uniform
    date_info["day"] = date_info["day"].zfill(2)
    date_info["month"] = date_info["month"].lower()
    return date_info


def extract(raw_input, processed_output_path):
    raw_input = Path(raw_input)
    processed_output_path = Path(processed_output_path)
    processed_output_path.mkdir(exist_ok=True, parents=True)
    existing_files = {str(file).partition("--")[2][:-4] for file in processed_output_path.glob("**/*.txt")}
    for html_file in raw_input.glob("*.html"):
        if html_file.stem in existing_files:
            continue

        try:
            all_dialogs, author, date, date_info, title = parse_document(html_file)
        except Exception as exc:
            logger.warning("Could not parse %s: %s", html_file, exc)
            continue

        output_file = (
            processed_output_path / date_info["year"] / date_info["month"] / f"{date_info['day']}--{html_file.stem}.txt"
        )
        output_file.parent.mkdir(exist_ok=True, parents=True)
        with open(output_file, "w") as writable:
            writable.write(title + "\n")
            writable.write(author + "\n")
            writable.write(date + "\n")
            for speaker, lines in all_dialogs:
                writable.write("---\n")
                speaker = speaker or "???"
                writable.write(speaker + "\n")
                for line in lines:
                    writable.write(line + "\n")


def _c(txt: str) -> str:
    """Clean a string removing whitespace"""
    return txt.replace("\xa0", " ").replace("\xc2", " ").strip()


def _parse_ps(ps: Tag) -> Tuple[str, str]:
    raw_speaker, _, raw_dialog = ps.text.partition(":")
    speaker = None
    dialog = _c(ps.text)
    if raw_speaker.isupper():
        speaker = _c(raw_speaker)
        dialog = _c(raw_dialog or "")
    if all((character == "-" for character in dialog)):
        dialog = None
    return speaker, dialog


def parse_document(file: Path):
    with open(file) as f:
        soup = BeautifulSoup(f.read(), "html5lib")

    article_content = soup.find("div", {"class": "article-body"})
    if not article_content:
        divs = soup.find_all("div", {"class": "pull-left"})
        if len(divs) == 2:
            article_content = divs[0]
        elif len(divs) >= 3:
            article_content = divs[1]
        elif divs:
            article_content = divs[0]
        else:
            article_content = soup.find("article") or soup.find("body") or soup

    title_el = soup.find("h1")
    if not title_el:
        raise ValueError(f"Could not find title in document {file}")
    title = title_el.text.strip()

    author = None
    date = None

    # 1. Look across all sections for metadata boxes
    for sec in soup.find_all("section"):
        dds = sec.find_all("dd")
        if len(dds) >= 2:
            author = dds[0].text.strip()
            date = dds[1].text.strip()
            break
        elif len(dds) == 1 and not date:
            date = dds[0].text.strip()
        elif "|" in sec.text and not date:
            parts = [p.strip() for p in sec.text.split("|") if p.strip()]
            if len(parts) >= 2:
                author, date = parts[0], parts[1]
                break

    # 2. Look across all definition lists
    if not date or not author:
        for dl in soup.find_all("dl"):
            dts = [dt.text.strip().lower() for dt in dl.find_all("dt")]
            dds = [dd.text.strip() for dd in dl.find_all("dd")]
            for dt, dd in zip(dts, dds):
                if "autor" in dt and not author:
                    author = dd
                elif ("fecha" in dt or "publica" in dt) and not date:
                    date = dd
            if not date and len(dds) >= 2:
                if not author:
                    author = dds[0]
                date = dds[1]
                break

    # 3. Check author meta tags
    if not author:
        meta_author = soup.find("meta", {"name": "author"})
        if meta_author and meta_author.get("content"):
            author = meta_author["content"].strip()
    if not author:
        author = "Presidencia de la República"

    # 4. Fallback for date from title, meta tags, or filename stem
    if not date or not date_format.search(date):
        if title and date_format.search(title):
            match = date_format.search(title)
            date = f"{int(match.group('day'))} de {match.group('month').lower()} de {match.group('year')}"
        if not date:
            og_title = soup.find("meta", {"property": "og:title"})
            if og_title and og_title.get("content") and date_format.search(og_title["content"]):
                match = date_format.search(og_title["content"])
                date = f"{int(match.group('day'))} de {match.group('month').lower()} de {match.group('year')}"
        if not date:
            match = date_format.search(file.stem)
            if match:
                date = f"{int(match.group('day'))} de {match.group('month').lower()} de {match.group('year')}"

    if not date:
        raise ValueError(f"Could not find publication metadata in document {file}")

    all_ps = article_content.find_all("p") if article_content else []
    date_info = _parse_date(date)
    current_speaker = None
    all_dialogs = []
    dialogs = []
    for ps in all_ps:
        speaker, dialog = _parse_ps(ps)
        if speaker:
            if dialogs and current_speaker:
                all_dialogs.append((current_speaker, dialogs))
            current_speaker = speaker
            dialogs = [dialog] if dialog else []
        elif dialog:
            dialogs.append(dialog)

    if dialogs and current_speaker:
        all_dialogs.append((current_speaker, dialogs))
    elif dialogs:
        all_dialogs.append((None, dialogs))

    return all_dialogs, author, date, date_info, title
