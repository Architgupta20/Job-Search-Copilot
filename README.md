# Job Search Copilot

Local-first recruiter tool. Upload a resume once, then **search a company** (LinkedIn people, email research, careers jobs) or **tailor your resume to a job description** — using only facts from your upload.

Runs at **http://localhost:3000**. Data stays in local `data/` (gitignored).

**Repo:** https://github.com/Architgupta20/Job-Search-Copilot  
**Live site:** https://job-search-copilot-seven.vercel.app/ (frontend on Vercel; Python agents pending Render)

---

## Features

### Path A — Company search

- **Company name + roles** — pick one or more profiles (tech, product, leadership, business)
- **LinkedIn people** — up to **10 senior profiles per role**, filtered to that role or close equivalents (e.g. AI Engineer → ML / GenAI / Head of AI), ranked Director / Head / Principal first
- **Contact research** (automatic) — tries **Hunter.io**, **Google/SerpAPI**, and **company web pages** for email; shows all findings + confidence
- **Outreach drafts** — separate UI boxes for **cold email** (full format with subject) and **LinkedIn message** (connection/InMail note)
- **Jobs** — only that company’s careers portal (auto-detected: company site, Greenhouse, Lever, Ashby)
- **ATS %** and **Tailor my resume** per job when a resume is uploaded
- **Download CSV** of people + jobs

### Path B — Job description (JD)

- Paste a full JD → **ATS score**, **suggested edits**, editable draft
- Copy into your own Word file; optional plain **.docx** / **.txt** download
- DOCX upload on home recommended

---

## Architecture

| Part | Port | Role |
|------|------|------|
| **Python agents** (`agents/`) | 8000 | Resume parse, company search, contact enrichment, JD tailor |
| **Next.js UI** (`apps/web/`) | 3000 | UI + API proxy to Python |

API keys live in **`apps/web/.env`** only (loaded by `agents/app/env.py`).

---

## Prerequisites

| Tool | Notes |
|------|--------|
| [Node.js](https://nodejs.org/) | 20 LTS |
| [Python](https://www.python.org/) | 3.12 or Anaconda |
| [Groq](https://console.groq.com/keys) | JD tailor + outreach drafts (or Ollama / OpenAI) |
| [SerpAPI](https://serpapi.com) | LinkedIn people, jobs, web email search |
| [Hunter.io](https://hunter.io/api-keys) | Best email discovery (optional but recommended) |

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

Edit **`apps/web/.env`** (never commit):

```env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_key_here

# Company search + contact research
SERPAPI_API_KEY=your_serpapi_key
HUNTER_API_KEY=your_hunter_key
```

Verify keys:

```bash
cd agents
conda activate job-copilot
python scripts/check_groq.py
python scripts/check_hunter.py
```

### 3. Install

```bash
# Python
cd agents
conda create -n job-copilot python=3.12 -y
conda activate job-copilot
pip install -r requirements.txt

# Web
cd ../apps/web
npm install
```

### 4. Run

**Laptop slow or hanging?** Use lite mode (recommended on 8 GB Macs):

```bash
conda activate job-copilot
npm run dev:lite
```

This sets `JOB_COPILOT_LIGHT=1`: no Python file-watcher, webpack instead of Turbopack, skips careers scrape and bulk email research, max 3 people per role and 1 SerpAPI call per role. Use **Outreach drafts** for daily work.

Full dev (heavier):

```bash
conda activate job-copilot
npm run dev
```

- Agents: http://127.0.0.1:8000/health  
- UI: http://localhost:3000  

Stop with `Ctrl+C`.

### Or two terminals

```bash
# Terminal 1
cd agents && conda activate job-copilot
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2
cd apps/web && npm run dev
```

---

## Environment variables

All in **`apps/web/.env`** (see `.env.example`).

### LLM (pick one)

| Setup | Variables |
|--------|-----------|
| **Groq** | `LLM_PROVIDER=groq`, `GROQ_API_KEY` |
| **OpenAI** | `LLM_PROVIDER=openai`, `OPENAI_API_KEY` |
| **Ollama** (local) | `LLM_PROVIDER=ollama`, `OLLAMA_MODEL=llama3.2` |

### Company search & contacts

| Variable | Purpose |
|----------|---------|
| `SERPAPI_API_KEY` | LinkedIn people, careers/jobs discovery, Google email search in snippets |
| `HUNTER_API_KEY` | Hunter.io email finder + domain directory |

| Optional | Purpose |
|----------|---------|
| `PYTHON_API_URL` | Default `http://127.0.0.1:8000` |
| `GROQ_MODEL` | Default `llama-3.3-70b-versatile` |

**Phone numbers** are opportunistic (Hunter or scraped pages). There is no dedicated phone API wired in yet.

---

## How to use

1. **Home** — upload resume (PDF or DOCX).
2. **Company** — enter company, select role(s), search (30–90s with contact research).
3. Per person: review **Contact research**, click **Draft email + LinkedIn** → two separate copy boxes.
4. Per job: **ATS %**, **Tailor my resume**, **Open posting**.
5. **JD** — paste job description → ATS + edits → copy into Word.

---

## Project structure

```
Job-Search-Copilot/
├── agents/
│   ├── app/
│   │   ├── env.py              # loads apps/web/.env
│   │   ├── routers/
│   │   └── services/company/   # run, jobs, contact_enrichment, cold_email
│   └── scripts/
│       ├── check_groq.py
│       └── check_hunter.py
├── apps/web/                   # Next.js UI
├── scripts/dev.sh              # npm run dev
├── data/                       # gitignored
└── .env.example
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `503` / start Python agents | `uvicorn` on port 8000 or `npm run dev` |
| Groq `401` / restricted | New key, `check_groq.py`, or `LLM_PROVIDER=ollama` |
| Hunter fails | `python scripts/check_hunter.py`, credits on hunter.io |
| No LinkedIn people | `SERPAPI_API_KEY`, restart agents |
| No email found | Add `HUNTER_API_KEY` + `SERPAPI_API_KEY`; check Contact research panel |
| Search slow | Normal — contact research runs per person |
| `.venv` activate fails | Use `conda activate job-copilot` |

---

## Privacy

- Resumes and runs stay local in `data/`
- Never commit `apps/web/.env`
- Revoke API keys if exposed

---

## Docs

- [Architecture](Docs/ARCHITECTURE.md)
- [Recruiter setup](Docs/RECRUITER_SETUP.md)
- [Status](Docs/STATUS.md)

---

## License

Private / TBD
