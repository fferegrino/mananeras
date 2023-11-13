import re
from pathlib import Path
from typing import Tuple

from bs4 import BeautifulSoup, Tag

date_format = re.compile(r"(?P<day>[0-9]{2}) de (?P<month>[a-z]+) de (?P<year>[0-9]{4})")


def extract(raw_input, processed_output_path):
    raw_input = Path(raw_input)
    processed_output_path = Path(processed_output_path)
    processed_output_path.mkdir(exist_ok=True, parents=True)
    existing_files = {str(file).partition("--")[2][:-4] for file in processed_output_path.glob("**/*.txt")}
    for html_file in raw_input.glob("*.html"):
        if html_file.stem in existing_files:
            continue

        all_dialogs, author, date, date_info, title = parse_document(html_file)

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
    with open(file) as file:
        all_dialogs = []
        soup = BeautifulSoup(file.read(), "html5lib")
        divs = soup.find_all("div", {"class": "pull-left"})
        if len(divs) == 2:
            [article_content] = soup.find_all("div", {"class": "pull-left"})[:1]
        elif len(divs) == 3:
            [article_content] = soup.find_all("div", {"class": "pull-left"})[1:-1]

        title = soup.find("h1").text.strip()
        author, date = [dd.strip() for dd in article_content.find("section").text.split('|')]
        all_ps = article_content.find_all("p")
        date_info = date_format.match(date).groupdict()
        current_speaker = None
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
