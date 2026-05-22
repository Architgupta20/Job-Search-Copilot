# Job Search Copilot

Local-first tool for recruiters. Upload a resume once, then either **search a company** (people + job openings) or **tailor your resume to a job description** — without inventing experience.

Runs on your Mac at `http://localhost:3000`. Data stays on your machine.

---

## Features

### Path A — Company name

- Enter company name + target roles (AI Engineer, ML, Data Scientist, Data Analyst)
- **People:** CEOs, Program Managers, Lead AI Engineers, directors, recruiters — **current employees only** (no SDE1 / junior ICs)
- **Jobs:** matching roles from the company careers page (includes similar titles, e.g. GenAI Engineer)
- Contact email/phone only when found, with confidence labels

### Path B — Job description (JD)

- Paste a full JD
- Tailors resume using **only facts from your upload** (no false skills or employers)
- ATS-style keyword score (supported keywords only)
- Download tailored resume as **Word (.docx)** or plain text
- **Best formatting:** upload resume as **DOCX** (not PDF)

---

## Prerequisites

| Tool | Version |
|------|---------|
| [Git](https://git-scm.com/) | any recent |
| [Node.js](https://nodejs.org/) | 20 LTS |
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | optional (Postgres later; not required for current features) |

---

## Quick start

### 1. Clone

```bash
git clone https://github.com/YOUR_USERNAME/Job-Search-Copilot.git
cd Job-Search-Copilot
```

### 2. Install web app

```bash
cd apps/web
npm install
```

### 3. Configure API keys

```bash
cp ../../.env.example .env
# Or create apps/web/.env directly — see Environment variables below
```

Edit **`apps/web/.env`** (never commit this file).

### 4. Run

**Recommended — Python agents + web UI:**

```bash
# Terminal 1
cd agents
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 2
cd apps/web
npm run dev
```

Open **http://localhost:3000**. The web app requires Python agents on port 8000.

---

## Environment variables

Create **`apps/web/.env`** (copy from `.env.example` at repo root).

### Required for JD tailoring (pick one LLM)

| Variable | Provider | Get key |
|----------|----------|---------|
| `LLM_PROVIDER=groq` + `GROQ_API_KEY` | **Groq** (recommended, free tier) | [console.groq.com/keys](https://console.groq.com/keys) |
| `LLM_PROVIDER=ollama` + `OLLAMA_MODEL=llama3.2` | **Ollama** (local, no key) | [ollama.com](https://ollama.com) |
| `LLM_PROVIDER=openrouter` + `OPENROUTER_API_KEY` | OpenRouter | [openrouter.ai/keys](https://openrouter.ai/keys) |
| `LLM_PROVIDER=anthropic` + `ANTHROPIC_API_KEY` | Anthropic | [console.anthropic.com](https://console.anthropic.com/) |
| `LLM_PROVIDER=gemini` + `GEMINI_API_KEY` | Google Gemini | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `LLM_PROVIDER=openai` + `OPENAI_API_KEY` | OpenAI | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |

If one provider hits quota, set `LLM_PROVIDER` to another or add a second key (Groq + Ollama are good fallbacks).

### Optional — better company people search

| Variable | Purpose |
|----------|---------|
| `SERPAPI_API_KEY` | LinkedIn people via SerpAPI — [serpapi.com](https://serpapi.com) |

### Optional — Python agents URL

| Variable | Purpose |
|----------|---------|
| `PYTHON_API_URL` | FastAPI agents base URL (default `http://127.0.0.1:8000`) |

### Optional — database (future)

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Postgres via `docker compose up -d` at repo root |

---

## Project structure

```
Job-Search-copilot/
├── agents/                # Python FastAPI agents (resume, company, JD)
│   └── app/               # Routers + services (LLM, scrape, docx)
├── apps/web/              # Next.js UI + API proxy to Python agents
│   ├── app/               # Pages (home, company, jd) + API routes
│   ├── lib/
│   │   ├── python-api.ts  # Proxy to agents/
│   │   ├── resume/        # Session + types (UI)
│   │   ├── company/       # Types (UI)
│   │   └── jd/            # Types (UI)
│   └── .env               # Your secrets (gitignored)
├── data/                  # Local resumes & run results (gitignored)
├── docs/
│   ├── ARCHITECTURE.md
│   └── RECRUITER_SETUP.md
├── docker-compose.yml     # Postgres (optional)
├── .env.example
└── README.md
```

---

## How to use

1. **Upload resume** (DOCX preferred for download formatting)
2. Choose:
   - **Company name** → search people + careers jobs
   - **Job description** → tailor + download Word file
3. Re-upload resume on home to change file

---

## Development

```bash
cd apps/web
npm run dev      # http://localhost:3000
npm run build    # production build
npm run lint     # ESLint
```

### Optional: Postgres

```bash
# From repo root
docker compose up -d
```

Not required for current upload / company / JD features (data is stored under `data/`).

---

## Privacy

- Resumes and run outputs live under `data/` on your computer (gitignored)
- Do **not** commit `.env` or API keys to GitHub
- Each recruiter should use their own API keys in their own `.env`

---

## Roadmap

- [ ] Cold email draft on company results
- [ ] Application history UI
- [ ] Postgres persistence for runs
- [ ] PDF download with original layout

---

## Docs

- [Architecture](docs/ARCHITECTURE.md)
- [Recruiter setup](docs/RECRUITER_SETUP.md)

---

## License

Private / TBD
