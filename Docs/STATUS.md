# Project status

Last updated: May 2026

## Working

- Resume upload (PDF + DOCX) with local parsing
- Company search: people (senior only, same company filter) + careers jobs
- JD tailor via Groq / OpenAI (Python + TypeScript)
- Download tailored resume (.docx, .txt)
- SerpAPI for LinkedIn people (optional)
- **Python agents** (`agents/`) — FastAPI on port 8000; required for all API features

## Config

- API keys in `apps/web/.env` only (loaded by Python agents too)
- Recommended: `LLM_PROVIDER=groq`, `GROQ_API_KEY`, `SERPAPI_API_KEY`
- Upload **DOCX** for best Word download formatting

## Run

```bash
# Terminal 1 — Python agents
cd agents && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000

# Terminal 2 — Web UI
cd apps/web && npm run dev
```

Without agents running, API calls return 503 with setup instructions.

## Next

- Cold email draft
- Fix edge cases in Word export
- Application history
