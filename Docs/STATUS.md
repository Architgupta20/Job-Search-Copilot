# Project status

Last updated: May 2026

## Working

- Resume upload (PDF + DOCX) with local parsing
- Company search: people (senior only, same company filter) + careers jobs
- SerpAPI disk cache for repeat searches (configurable TTL in `.env`)
- JD tailor via Groq / OpenAI / Ollama (Python agents)
- Download tailored resume (.docx, .txt)
- Application tracker (local device storage)
- Cover letter generator (fact-only, optional JD)
- Interview prep — 5 questions + STAR prompts from resume
- Outreach agent on tracker — next actions + resume-backed drafts
- Cold email + LinkedIn drafts, Hunter email lookup
- **Python agents** (`agents/`) — FastAPI on port 8000; required for all API features

## Config

- API keys in `apps/web/.env` only (loaded by Python agents too)
- Recommended: `LLM_PROVIDER=groq`, `GROQ_API_KEY`, `SERPAPI_API_KEY`
- Optional: `SERPAPI_CACHE_TTL_HOURS`, `HUNTER_API_KEY`
- Upload **DOCX** for best Word download formatting

## Run

```bash
conda activate job-copilot
npm run dev:lite
```

Without agents running, API calls return 503 with setup instructions.

## Next

- Beta deploy (hosted UI + agents)
- Word export edge cases
