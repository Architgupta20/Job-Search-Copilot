# Architecture

## Components

| Layer | Path | Role |
|-------|------|------|
| Web UI | `apps/web` | Next.js pages and forms |
| API proxy | `apps/web/app/api/*` | Forwards requests to Python agents |
| Agents | `agents/` | FastAPI — resume parse, company search, JD tailor, DOCX export |
| Data | `data/` | Local resumes and run JSON (gitignored) |

## Flow

1. User uploads resume in the browser → `POST /api/resume/upload` → Python parses and stores under `data/resumes/`.
2. **Company path** → `POST /api/run/company` → Python resolves site, scrapes careers, SerpAPI/LLM for people.
3. **JD path** → `POST /api/run/jd` → Python LLM tailors text → `GET /api/run/jd/{id}/download` for `.docx` / `.txt`.

## Configuration

All secrets in `apps/web/.env`. Python loads the same file via `agents/app/config.py`.

## Run locally

Both processes required:

- `uvicorn app.main:app --port 8000` (agents)
- `npm run dev` in `apps/web` (UI on port 3000)
