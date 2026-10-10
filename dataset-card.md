---
license: cc-by-sa-4.0
pretty_name: Conferencias Mañaneras
language:
- es
tags:
- government
- politics
- mexico
size_categories:
- 1K<n<10K
---

# Conferencias Mañaneras

Las versiones estenográficas de las conferencias de prensa matutinas de la presidencia de México, descargadas diariamente del [archivo de la presidencia en gob.mx](https://www.gob.mx/presidencia/es/archivo/articulos) y convertidas a texto plano para hacerlas un poco más fáciles de consumir programáticamente.

Hay un archivo por conferencia en `AAAA/mes/DD--slug.txt`, por ejemplo `2026/octubre/09--version-estenografica-conferencia-de-prensa-de-la-presidenta-claudia-sheinbaum-pardo-del-09-de-octubre-de-2026.txt`, donde `slug` es la última parte de la URL del artículo en gob.mx.

Cada archivo tiene el título, el autor y la fecha en sus tres primeras líneas, seguidos de las participaciones: cada una empieza con una línea `---`, luego el nombre de quien habla (`???` si no se pudo identificar) y después sus párrafos, uno por línea.

```
Versión estenográfica. Conferencia de prensa de la presidenta Claudia Sheinbaum Pardo del 09 de octubre de 2026
Presidencia de la República
09 de octubre de 2026
---
PRESIDENTA DE MÉXICO, CLAUDIA SHEINBAUM PARDO
Buenos días.
---
PREGUNTA
...
```

## Uso

```python
from huggingface_hub import snapshot_download
from mananeras.reader import todas

ruta = snapshot_download("feregrino/mananeras", repo_type="dataset")
for conferencia in todas(ruta):
    print(conferencia.fecha, conferencia.titulo)
```

`mananeras.reader` viene del repositorio [fferegrino/mananeras](https://github.com/fferegrino/mananeras), que también tiene el código que genera el dataset. También disponible en [Kaggle](https://www.kaggle.com/datasets/ioexception/mananeras).
