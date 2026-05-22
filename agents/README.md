# Python agents

FastAPI service for resume parsing, company search, and JD tailoring. The Next.js app proxies to this service when it is running on port **8000**.

## Setup (Conda — recommended on Mac with Anaconda)

```bash
cd agents
conda create -n job-copilot python=3.12 -y
conda activate job-copilot
pip install -r requirements.txt
```

API keys live in **`apps/web/.env`** (same as the web app). The agents load that file automatically.

### Groq 401 but key “looks right”?

Run `python scripts/check_groq.py` — it prints a **fingerprint**. If you create new Groq keys but the fingerprint **does not change**, the new key was not saved to `apps/web/.env` (use `nano` to edit and save).

If Groq still returns 401 after a saved new key, use **Ollama** (free, local, no API key):

```bash
# Install Ollama from https://ollama.com, then:
ollama pull llama3.2
```

In `apps/web/.env`:

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
```

Comment out or remove `GROQ_API_KEY` lines, restart uvicorn.

## Run

```bash
cd agents
conda activate job-copilot
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health check: http://127.0.0.1:8000/health

## With the web UI

**Terminal 1 — agents:**

```bash
cd agents && conda activate job-copilot && uvicorn app.main:app --reload --port 8000
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
