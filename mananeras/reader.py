from pathlib import Path
from typing import Union, List, Iterator

from mananeras.entities import Mananera, Participacion


def lee_mananera(path: Union[Path, str]) -> Mananera:
    path = Path(path)

    with open(path) as readable:
        title = next(readable).strip()
        author = next(readable).strip()
        date = next(readable).strip()

        participaciones: List[Participacion] = []
        speaker:str = None
        dialogs: List[str] = []
        for line in readable:
            if line.strip() == '---' and speaker is not None:
                participaciones.append(Participacion(speaker, dialogs))
                speaker = None
                dialogs = []
            elif speaker is None:
                speaker = line.strip()
            elif speaker is not None:
                dialogs.append(line.strip())
        if speaker is not None:
            participaciones.append(Participacion(speaker, dialogs))

    return Mananera(titulo=title, autor=author, date_string=date, participaciones=participaciones)

def todas(path: Union[Path, str] = "articulos") -> Iterator[Mananera]:
    path = Path(path)
    if not path.is_dir():
        raise ValueError(f"La ruta {str(path)} no es un directorio")

    for file in path.glob("**/*.txt"):
        yield lee_mananera(file)


def lee_todas(path: Union[Path, str] = "articulos") -> List[Mananera]:
    mananeras = [conf for conf in todas(path)]
    return mananeras

