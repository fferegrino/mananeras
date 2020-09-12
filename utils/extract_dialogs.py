from pathlib import Path
import re

from bs4 import BeautifulSoup

date_format = re.compile(r"(?P<day>[0-9]{2}) de (?P<month>[a-z]+) de (?P<year>[0-9]{4})")

def extract(raw_input, processed_output):
    raw_input = Path(raw_input)
    processed_output = Path(processed_output)
    processed_output.mkdir(exist_ok=True, parents=True)
    existing_files = {str(file).partition("--")[2][:-4] for file in processed_output.glob("**/*.txt")} 
    for html_file in raw_input.glob("*.html"):
        if html_file.stem in existing_files:
            continue

        author = None
        date = None
        title = None
        all_dialogs = []
        with open(html_file) as file:
            soup = BeautifulSoup(file.read(), "html5lib")
            [article_content] = soup.find_all("div", {"class": "pull-left"})[1:-1]
            title = soup.find("h1").text.strip()
            author, date = [dd.text.strip() for dd in soup.find("section", {"class":"border-box"}).find_all("dd")]
            all_ps = article_content.find_all("p")


            date_info = date_format.match(date).groupdict()
            file = processed_output / date_info["year"] / date_info["month"] / f"{date_info['day']}--{html_file.stem}.txt"

            current_speaker = None
            dialogs = []
            for ps in all_ps:
                speaker = ps.find("strong")
                if speaker:
                    if dialogs and current_speaker:
                        all_dialogs.append((current_speaker, dialogs))
                    current_speaker = speaker.text.strip(": ")
                    dialogs = []
                else:
                    dialogs.append(ps.text.strip())

        file.parent.mkdir(exist_ok=True, parents=True)
        with open(file, "w") as writable:
            writable.write(title + "\n")
            writable.write(author + "\n")
            writable.write(date + "\n")
            for speaker, lines in all_dialogs:
                writable.write("---\n")
                writable.write(speaker + "\n")
                for line in lines:
                    writable.write(line + "\n")
