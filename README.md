# SIMCA Analytics — versión web (costo $0)

Monorepo: **frontend** Next.js (Vercel Hobby) + **backend** FastAPI/Playwright (Hugging Face Spaces, Docker) + paquete de negocio **`simca/`** reutilizado.

```
simca/        núcleo (models, parsers, matrix, requisitos, snapshot, config_store…) — scraper ahora async, sin escritura a disco
backend/      main.py (API), service.py (JSON para el front), Dockerfile, tests
frontend/     Next.js App Router + TypeScript + Tailwind (persistencia en localStorage)
scripts/      stage_space.sh  (arma la carpeta plana que exige Hugging Face)
```

## Qué cambió respecto a la versión Streamlit
| Antes | Ahora |
|---|---|
| `playwright.sync_api` | `playwright.async_api` (`simca/scraper.py`) |
| `ultimo_error.html`, `filelock`, `.bak`, `fileio.py`, `state.py`, `settings` con `.env`/data dir | eliminados; `config_store.py` y `snapshot.py` quedan como lógica pura (sanitización / armado del JSON) |
| `pandas` (`matriz_a_dataframe`) | `matriz_a_filas()`; el CSV lo genera el navegador |
| credenciales en `.env` | solo en el cuerpo de `POST /api/scrape`, en memoria, nunca logueadas ni devueltas |
| `views/matriz.py`, `views/configuracion.py` | componentes React (`Matrix`, `Pendientes`, `MateriaEditor`…) |
| JSON en disco | `localStorage` + exportar/importar respaldo `.json` |

La lógica de `parsers.py`, `matrix.py` y `requisitos.py` **no se modificó** (salvo quitar pandas).
Extra: "simular aprobada" (inyecta una nota sintética 5.0 solo para el cálculo; el promedio sigue siendo el real).

## API
- `GET /health`
- `POST /api/scrape` `{usuario, password, codigo_estudiante, config?, simuladas?}` → `{snapshot, matriz, requisitos, pendientes, …}`
- `POST /api/parse-manual` multipart: `notas`, `pensum`, `matriculadas?`, `config?`, `simuladas?`
- `POST /api/matrix/recalculate` `{snapshot, config?, simuladas?}`

Protecciones: CORS por `ALLOWED_ORIGINS`, límite por IP en `/api/scrape` (6 / 10 min), máx. 2 Chromium simultáneos, errores de validación sin eco de la contraseña, límite de 6 MB por HTML.

## Desarrollo local
```bash
# backend
pip install -r backend/requirements-dev.txt && playwright install chromium
cd backend && PYTHONPATH=.. uvicorn main:app --reload --port 7860
python -m pytest backend/tests            # 39 tests (sin red ni Chromium)

# frontend
cd frontend && cp .env.example .env.local && npm install && npm run dev
```

## Despliegue
**1. Hugging Face Space (backend)**
1. Crea un Space → SDK **Docker** (blank), público o privado.
2. `bash scripts/stage_space.sh` y sube el contenido de `dist/space/` al repo del Space (o usa `.github/workflows/deploy-space.yml`: secret `HF_TOKEN`, variable `HF_SPACE=usuario/space`).
3. En *Settings → Variables*: `ALLOWED_ORIGINS=https://tu-app.vercel.app` (y opcional `ALLOWED_ORIGIN_REGEX` para previews).
4. URL del backend: `https://<usuario>-<space>.hf.space`.

**2. Vercel (frontend)**: importa el repo, *Root Directory* = `frontend`, variable `NEXT_PUBLIC_API_URL` = URL del Space. Redeploy.

## Límites conocidos del plan gratuito
- El Space se duerme tras ~48 h sin uso; despertar tarda 1–3 min (el indicador del header lo muestra).
- SIMCA puede bloquear IPs de datacenter: usa la pestaña **Subir HTML**.
- Datos personales (notas) viven en el `localStorage` del navegador: quien use el mismo perfil del navegador puede verlos.
