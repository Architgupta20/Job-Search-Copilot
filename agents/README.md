# Python agents

FastAPI service for resume parsing, company search, and JD tailoring. The Next.js app proxies to this service when it is running on port **8000**.

## Setup

```bash
cd agents
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

API keys live in **`apps/web/.env`** (same as the web app). The agents load that file automatically.

## Run

```bash
cd agents
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health check: http://127.0.0.1:8000/health

## With the web UI

**Terminal 1 — agents:**

```bash
cd agents && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — web:**

```bash
cd apps/web && npm run dev
```

Open http://localhost:3000. The UI calls Next.js API routes, which forward all agent work to this Python service.

Optional override in `apps/web/.env`:

```
PYTHON_API_URL=http://127.0.0.1:8000
```

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/resume/upload` | Parse and store resume |
| POST | `/api/company/run` | Company people + jobs |
| POST | `/api/jd/run` | Tailor resume to JD |
| GET | `/api/jd/{runId}/download?format=docx\|txt` | Download tailored resume |
