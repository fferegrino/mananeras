from dataclasses import dataclass
from datetime import date, datetime
from typing import List

from dateparser import parse


@dataclass
class Participacion:
    hablante: str
    dialogos: List[str]


@dataclass
class Mananera:
    titulo: str
    autor: str
    date_string: str
    participaciones: List[Participacion]

    @property
    def fecha(self) -> date:
        a: datetime = parse(self.date_string, languages=["es"])
        return a.date()
