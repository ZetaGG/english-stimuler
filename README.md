# English Stimuler

Asistente personal para practicar inglés hablado: grabas tu voz leyendo un texto, y el sistema te devuelve transcripción, puntuación de pronunciación por palabra, errores gramaticales, feedback generado por IA y una estimación de banda IELTS.

## Qué hace

- **Transcripción** del audio con `faster-whisper` (local, sin enviar el audio a ningún servicio).
- **Pronunciación** evaluada a nivel de fonema con `allosaurus`, alineada contra la transcripción esperada para detectar las palabras concretas que fallan.
- **Gramática** con LanguageTool, listando cada error con su categoría, mensaje y sugerencias.
- **Feedback** en lenguaje natural vía OpenRouter (modelo configurable).
- **Banda IELTS** estimada en cuatro ejes — fluidez (WPM), riqueza léxica, pronunciación y gramática — con interpolación entre puntos de corte.
- **Historial y vocabulario**: cada evaluación se guarda en SQLite, con estadísticas agregadas y una lista de palabras a reforzar.

## Arquitectura

El backend sigue una separación por capas, con las dependencias apuntando siempre hacia el dominio:

```
server/src/app/
├── domain/          # Reglas puras: métricas, bandas IELTS, modelos. Sin I/O.
├── application/     # Casos de uso: evaluation, history, vocabulary.
├── infrastructure/  # Adaptadores: whisper, allosaurus, LanguageTool, OpenRouter, SQLite.
└── interfaces/      # FastAPI: routers y validación de entrada.
```

El frontend (`apps/web`) es React + TypeScript + Vite, sin framework de UI, y consume la API a través del proxy de desarrollo.

## Requisitos

- Python 3.11+ y [uv](https://docs.astral.sh/uv/)
- Node.js 20+
- Docker (solo para LanguageTool)

## Puesta en marcha

**1. LanguageTool**

```bash
docker compose up -d languagetool
```

Queda escuchando en `http://localhost:8010`.

**2. Backend**

```bash
cd server
uv sync --all-groups
cp .env.example .env        # y pon tu OPENROUTER_API_KEY
make dev                    # http://localhost:8001
```

**3. Frontend**

```bash
cd apps/web
npm install
npm run dev                 # http://localhost:5173
```

## Variables de entorno

Definidas en `server/.env`:

| Variable | Por defecto | Descripción |
|---|---|---|
| `OPENROUTER_API_KEY` | — | Necesaria para el feedback con IA. Sin ella, el resto funciona. |
| `FEEDBACK_MODEL` | `openai/gpt-4o-mini` | Modelo usado para generar el feedback. |
| `DATABASE_PATH` | `data/english_stimuler.db` | Ruta del SQLite. |

## API

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/health` | Estado del servicio. |
| `POST` | `/v1/evaluate` | Evalúa un audio (`multipart`: `expected_text`, `audio`, `segments` opcional). |
| `GET` | `/v1/evaluations` | Historial de evaluaciones. |
| `GET` | `/v1/evaluations/{id}` | Detalle de una evaluación. |
| `DELETE` | `/v1/evaluations/{id}` | Borra una evaluación. |
| `GET` | `/v1/stats` | Estadísticas agregadas. |
| `GET` | `/v1/vocabulary` | Palabras a reforzar. |
| `DELETE` | `/v1/vocabulary/{word}` | Quita una palabra de la lista. |

Documentación interactiva en `http://localhost:8001/docs`.

## Tests

```bash
cd server && uv run pytest     # 187 tests, cobertura mínima exigida: 80%
cd apps/web && npm test        # vitest
cd apps/web && npx tsc --noEmit
```

CI en GitHub Actions corre ambas suites en cada push y pull request.

## Estado

Proyecto personal en desarrollo activo. Sin licencia definida por ahora.
