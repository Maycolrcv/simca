# SIMCA Analytics

Cruza el **pensum oficial** con la **historia académica** de SIMCA (Unicauca) y muestra una matriz
de avance (aprobada / disponible / bloqueada / reprobada) con alias y prerrequisitos editables.

## Estructura
```
app.py                    entrada Streamlit (navegación + init de session_state)
views/matriz.py           página principal: matriz, métricas, exportación
views/configuracion.py    alias y prerrequisitos por materia
simca/settings.py         dotenv, rutas, directorio privado
simca/scraper.py          Playwright: login -> buscar -> Historia Académica / Pénsum (solo HTML)
simca/cli_scrape.py       subproceso que scrapea y guarda el snapshot
simca/parsers.py          BeautifulSoup: parse_pensum_html / parse_notas_html
simca/snapshot.py         unificación base pensum+notas -> JSON local
simca/matrix.py           emparejamiento, prerrequisitos efectivos, estados, métricas
simca/config_store.py     config_materias.json: lock + escritura atómica + fusión por materia
simca/render.py           HTML de la matriz (escapado)
des_not.py                CLI compatible: exporta aprobadas a CSV
tests/                    pytest (HTML sintético, sin datos personales)
```

## Puesta en marcha
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env        # completa SIMCA_USER y SIMCA_PASSWORD (comillas simples si tiene # $ o espacios)
streamlit run app.py
```
Sin conexión: en la barra lateral, "Cargar HTML guardados" acepta los `.html` de Pénsum e Historia Académica.

## Seguridad
- Credenciales solo por `.env`/entorno (python-dotenv); no existen valores en el código ni se imprimen.
- Datos locales en `data/` (o `SIMCA_DATA_DIR`, recomendado fuera del repo): permisos 0700/0600 y un
  `.gitignore` interno con `*`. El `.gitignore` raíz excluye `.env`, `data/`, `*.csv`, `SIMCA_*.html`, `NOTAS.txt`, etc.
- El snapshot NO guarda cédula ni código del estudiante.
- **Los archivos `NOTAS.txt`, `PENSUM.txt` y `CODIGO_DEMO.html` originales contienen usuario y contraseña en texto plano
  y cookies de sesión: no los subas; cambia esa contraseña y, si ya estuvieron en un repositorio, purga el historial.**

## Persistencia (`config_materias.json`)
```json
{"version": 1, "revision": 3, "materias": {"21505": {"aliases": ["Lecto - Escritura"], "prereqs_extra": [], "prereqs_removidos": []}}}
```
La clave es el ID interno de SIMCA. Un alias puede ser un nombre antiguo **o el ID** con que aparece en la historia.
Se lee una vez al iniciar la sesión y solo se escribe al guardar.

## Pruebas
`pip install -r requirements-dev.txt && pytest`
