# Deploy (Vercel + Render)

Two hosts: **Vercel** = website, **Render** = Python agents.

---

## Part A — Render (backend first)

1. Go to [render.com](https://render.com) → sign in with GitHub.
2. **New** → **Web Service** → select **Job-Search-Copilot** repo.
3. Settings:
   - **Name:** `job-copilot-agents` (any name)
   - **Runtime:** **Docker**
   - **Dockerfile path:** `agents/Dockerfile`
   - **Docker context:** `.` (repo root)
   - **Health check path:** `/health`
4. **Environment** → add variables (same keys as `apps/web/.env`):

   | Key | Example |
   |-----|---------|
   | `LLM_PROVIDER` | `groq` |
   | `GROQ_API_KEY` | your key |
   | `SERPAPI_API_KEY` | your key |
   | `HUNTER_API_KEY` | your key (optional) |
   | `ALLOWED_ORIGINS` | leave empty for now; add Vercel URL after Part B |

5. **Disk** (optional but recommended): mount **`/app/data`** (1 GB) so resumes and SerpAPI cache survive restarts.
6. Click **Create Web Service** and wait for deploy.
7. Copy your agents URL, e.g. `https://job-copilot-agents.onrender.com`
8. Test: open `https://YOUR-AGENTS-URL.onrender.com/health` → should show `"status": "ok"`.

---

## Part B — Vercel (frontend)

1. Go to [vercel.com](https://vercel.com) → **Add New** → **Project**.
2. Import **Job-Search-Copilot** from GitHub.
3. **Root Directory:** click **Edit** → set to **`apps/web`**.
4. **Environment Variables** → add:

   | Key | Value |
   |-----|--------|
   | `PYTHON_API_URL` | `https://YOUR-AGENTS-URL.onrender.com` (no trailing slash) |

5. Click **Deploy**.
6. Copy your site URL, e.g. `https://job-search-copilot.vercel.app`.

---

## Part C — Connect them

1. Back on **Render** → your service → **Environment**.
2. Set:
   ```env
   ALLOWED_ORIGINS=https://YOUR-SITE.vercel.app
   ```
3. Save (Render redeploys automatically).

---

## Smoke test

On your Vercel URL:

1. Upload a resume  
2. Run one company search or JD tailor  

If you see **503 / start Python agents**, check `PYTHON_API_URL` on Vercel and that Render `/health` is OK.

---

## Notes

- **Secrets** live on Render and Vercel dashboards — never commit `.env`.
- **Tracker** is still browser-only until a later step (Postgres).
- **Free Render** may sleep after idle; first request can be slow (~30s).
