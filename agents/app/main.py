from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import company, jd, resume

app = FastAPI(
    title="Job Search Copilot Agents",
    description="Python agents for resume, company search, and JD tailoring.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resume.router)
app.include_router(company.router)
app.include_router(jd.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "agents"}
