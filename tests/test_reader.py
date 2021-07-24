from datetime import date
from pathlib import Path

from mananeras.reader import lee_mananera


def test_read_mananera(sample_docs_path: Path):

    mananera = lee_mananera(sample_docs_path / "ejemplo.txt")

    assert mananera.fecha == date(2019, 8, 2)
    assert mananera.titulo == "Versión estenográfica. Diálogo con la Comunidad del Hospital Rural de Metepec, Hidalgo"

    assert len(mananera.participaciones) == 3
    assert mananera.participaciones[-1].hablante == "PRESIDENTE ANDRÉS MANUEL LÓPEZ OBRADOR"
    assert mananera.participaciones[-1].dialogos[-1] == "Muchas gracias."
    assert mananera.participaciones[-2].dialogos[-1] == "Presidente, la unidad hace que Hidalgo crezca."
