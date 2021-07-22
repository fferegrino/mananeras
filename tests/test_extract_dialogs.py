from urllib.request import urlretrieve
from pathlib import Path

import pytest
from _pytest.config import Config

from utils.extract_dialogs import parse_document

@pytest.fixture
def sample_docs_path(pytestconfig: Config) -> Path:
    return Path(pytestconfig.rootdir / "tests"/ "sample_docs")

def test_2019(sample_docs_path: Path):
    # https://www.gob.mx/presidencia/es/articulos/version-estenografica-de-la-conferencia-de-prensa-matutina-miercoles-11-de-septiembre-2019
    file = sample_docs_path / "conferencia-11-de-septiembre-2019.html"
    all_dialogs, author, date, date_info, title = parse_document(file)

    assert title == 'Versión estenográfica de la conferencia de prensa matutina | Miércoles 11 de septiembre, 2019'
    assert date_info == {'day': '11', 'month': 'septiembre', 'year': '2019'}
    assert author == 'Presidencia de la República'

    assert all_dialogs[0][0] == "PRESIDENTE ANDRÉS MANUEL LÓPEZ OBRADOR"
    assert all_dialogs[0][1][0] == "Buenos días. Ánimo."

    assert all_dialogs[-1][0] == "PRESIDENTE ANDRÉS MANUEL LÓPEZ OBRADOR"
    assert all_dialogs[-1][1][-1] == "Muy bien, muchas gracias."

    assert all_dialogs[-2][0] == "INTERLOCUTOR"
    assert all_dialogs[-2][1][0] == "(Inaudible)"


def test_2021(sample_docs_path: Path):
    # https://www.gob.mx/presidencia/es/articulos/version-estenografica-conferencia-de-prensa-del-presidente-andres-manuel-lopez-obrador-del-28-de-junio-de-2021
    file = sample_docs_path / "conferencia-28-de-junio-de-2021.html"
    all_dialogs, author, date, date_info, title = parse_document(file)

    assert title == 'Versión estenográfica. Conferencia de prensa del presidente Andrés Manuel López Obrador del 28 de junio de 2021'
    assert date_info == {'day': '28', 'month': 'junio', 'year': '2021'}
    assert author == 'Presidencia de la República'

    assert all_dialogs[0][0] == "PRESIDENTE ANDRÉS MANUEL LÓPEZ OBRADOR"
    assert all_dialogs[0][1][0] == "Buenos días."

    assert all_dialogs[-1][0] == "PRESIDENTE ANDRÉS MANUEL LÓPEZ OBRADOR"
    assert all_dialogs[-1][1][-1] == "En la mañana el gobernador de Chihuahua y en la tarde-noche el gobernador de Jalisco."

    assert all_dialogs[-2][0] == "INTERLOCUTORA"
    assert all_dialogs[-2][1][0] == "¿A qué hora?"