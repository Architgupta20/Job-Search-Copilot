# Recruiter setup (local)

## 1. Install

- Git, Node.js 20+, VS Code (optional)
- Docker Desktop (optional — only for Postgres later)

## 2. Clone and install

```bash
git clone <your-repo-url>
cd Job-Search-Copilot/apps/web
npm install
```

## 3. API keys

Create `apps/web/.env` — see [README](../README.md#environment-variables).

Minimum for full app:

```env
SERPAPI_API_KEY=your_key
LLM_PROVIDER=groq
GROQ_API_KEY=your_key
```

## 4. Run

```bash
# Terminal 1 — Python agents
cd agents
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Web UI
cd apps/web
npm run dev
```

Open http://localhost:3000

## 5. Tips

- Upload resume as **DOCX** for best tailored download
- After code updates, **tailor again** and download a new file (old downloads may be invalid)
- Never share or commit `.env`

See also [STATUS.md](STATUS.md) for what is implemented.
