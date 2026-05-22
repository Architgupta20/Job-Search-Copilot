# Job Search Copilot

Local-first tool for recruiters. Upload a resume once, then either **search a company** (LinkedIn people + careers jobs) or **tailor your resume to a job description** — using only facts from your upload, nothing invented.

Runs on your Mac at **http://localhost:3000**. Data stays under `data/` on your machine (gitignored).

**Repo:** https://github.com/Architgupta20/Job-Search-Copilot

---

## Features

### Path A — Company search

- Enter a company name and select **one or more job profiles** (tech, product, leadership, and business roles)
- **LinkedIn people:** up to **10 profiles per selected role** (e.g. ML Engineer + AI Engineer → up to 20 people)
- **Draft cold email** per contact (uses resume facts when uploaded)
- **Download CSV** of people + jobs
- **Careers portal auto-detect** (company site, Greenhouse, Lever, Ashby via crawl + search)
- **Jobs:** openings **only for that company** (careers site + their Greenhouse/Lever board — random job boards filtered out)
- **ATS %** and **Tailor my resume** per job when a resume is uploaded
- Senior contacts only (leaders, recruiters) — not junior IC spam
- Requires **`SERPAPI_API_KEY`** for best LinkedIn results

### Path B — Job description (JD)

- Paste a full JD
- **ATS score** with matched vs missing keywords (supported facts only)
- **Suggested edits** in the UI (section, before/after, reason) — copy into **your own Word file**
- **Editable draft** textarea + **Copy all**
- Optional download: plain **.docx** or **.txt** (does not merge into your uploaded resume layout)
- Upload resume as **DOCX** on home for easiest manual updates

---

## Architecture

| Part | Port | Role |
|------|------|------|
| **Python agents** (`agents/`) | 8000 | Resume parse, company search, JD tailor, exports |
| **Next.js UI** (`apps/web/`) | 3000 | UI + API proxy to Python |

Both must be running (or use **`npm run dev`** from repo root — see below). API keys live in **`apps/web/.env`** only.

---

## Prerequisites

| Tool | Notes |
|------|--------|
| [Git](https://git-scm.com/) | any recent |
| [Node.js](https://nodejs.org/) | 20 LTS |
| [Python](https://www.python.org/) | 3.12 (or Anaconda) |
| [Groq API key](https://console.groq.com/keys) | recommended for JD tailor |
| [SerpAPI key](https://serpapi.com) | optional, better company people search |
| [Ollama](https://ollama.com) | optional, local LLM (no API key) |

---

## Quick start

### 1. Clone

```bash
git clone https://github.com/Architgupta20/Job-Search-Copilot.git
cd Job-Search-Copilot
```

### 2. API keys

```bash
cp .env.example apps/web/.env
```

Edit **`apps/web/.env`** (never commit this file):

```env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_key_here

# Optional — LinkedIn people (10 per role)
SERPAPI_API_KEY=your_serpapi_key
```

Test Groq key:

```bash
cd agents
conda activate job-copilot   # or your venv
python scripts/check_groq.py
```

Expect: `SUCCESS — Groq accepts this key.`

### 3. Run both servers (one command)

From repo root (with `job-copilot` conda env and `apps/web` dependencies installed):

```bash
conda activate job-copilot
npm run dev
```

This starts agents on **8000** and the web UI on **3000**. Stop with `Ctrl+C`.

### 3b. Or run separately

**Python agents (Terminal 1)**

**Conda (recommended on Mac with Anaconda):**

```bash
cd agents
conda create -n job-copilot python=3.12 -y
conda activate job-copilot
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Or venv:**

```bash
cd agents
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Check: http://127.0.0.1:8000/health → `{"status":"ok"}`

### 4. Web UI (Terminal 2)

```bash
cd apps/web
npm install
npm run dev
```

Open **http://localhost:3000**

---

## Environment variables

All in **`apps/web/.env`** (see `.env.example` at repo root).

### JD tailor (Python agents — pick one)

| Setup | Variables |
|--------|-----------|
| **Groq** (recommended) | `LLM_PROVIDER=groq`, `GROQ_API_KEY` |
| **OpenAI** | `LLM_PROVIDER=openai`, `OPENAI_API_KEY` |
| **Ollama** (local, free) | `LLM_PROVIDER=ollama`, `OLLAMA_MODEL=llama3.2` |

Python agents do **not** use Gemini/OpenRouter directly — use Groq, OpenAI, or Ollama.

### Company search

| Variable | Purpose |
|----------|---------|
| `SERPAPI_API_KEY` | LinkedIn people via Google/SerpAPI |

### Optional

| Variable | Purpose |
|----------|---------|
| `PYTHON_API_URL` | Default `http://127.0.0.1:8000` |
| `GROQ_MODEL` | Default `llama-3.3-70b-versatile` |

---

## How to use

1. **Home** — upload resume (DOCX preferred).
2. **Company** — pick roles → optional careers URL → search → CSV export, cold emails, ATS/tailor per job.
3. **JD** — paste description → get **ATS score** + suggestions → edit in UI → copy into your Word file (optional download).
4. Re-upload on home to change resume file.

---

## Project structure

```
Job-Search-Copilot/
├── agents/                 # FastAPI Python agents
│   ├── app/
│   │   ├── main.py
│   │   ├── env.py          # loads apps/web/.env
│   │   ├── routers/
│   │   └── services/       # company, jd, resume, llm
│   └── scripts/
│       └── check_groq.py
├── apps/web/               # Next.js UI + API proxy
│   ├── app/                # pages + API routes
│   └── lib/                # python-api, types, roles, session
├── data/                   # resumes & runs (gitignored)
├── Docs/
│   ├── ARCHITECTURE.md
│   ├── RECRUITER_SETUP.md
│   └── STATUS.md
└── .env.example
```

---

## Development

```bash
# Both (from repo root)
conda activate job-copilot && npm run dev

# Or separately
cd agents && conda activate job-copilot && uvicorn app.main:app --reload --port 8000
cd apps/web && npm run dev && npm run build && npm run lint
```

**Cursor/VS Code:** `.vscode/settings.json` disables auto-activate of a missing `agents/.venv`. Use `conda activate job-copilot` in the agents terminal.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `503` / start Python agents | Run uvicorn on port 8000 |
| Groq `401 Invalid API Key` | New key in `apps/web/.env`, `python scripts/check_groq.py`, restart uvicorn |
| `source .venv/bin/activate` fails | Use conda `job-copilot` or recreate venv |
| No LinkedIn people | Add `SERPAPI_API_KEY` |
| Few jobs found | Open careers portal link; some sites block scrapers |

---

## Privacy

- Resumes and runs stay in local `data/` (gitignored)
- Never commit `apps/web/.env` or API keys
- Revoke keys if they were ever pasted in chat or committed by mistake

---

## Docs

- [Architecture](Docs/ARCHITECTURE.md)
- [Recruiter setup](Docs/RECRUITER_SETUP.md)
- [Status](Docs/STATUS.md)

---

## License

Private / TBD
