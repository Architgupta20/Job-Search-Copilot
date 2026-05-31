from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.outreach_agent.run import run_outreach_agent
from app.services.resume.parser import load_resume

router = APIRouter(prefix="/api/outreach-agent", tags=["outreach-agent"])


class TrackerApplication(BaseModel):
    id: str
    company: str
    role: str
    status: str = "saved"
    contactName: str | None = None
    contactTitle: str | None = None
    contactEmail: str | None = None
    contactLinkedIn: str | None = None
    outreachSentAt: str | None = None
    notes: str | None = None


class OutreachAgentBody(BaseModel):
    resumeId: str
    applications: list[TrackerApplication] = Field(default_factory=list)
    confirmed: bool = False


@router.post("/run")
async def outreach_agent_run(body: OutreachAgentBody):
    if not body.confirmed:
        raise HTTPException(400, "Please confirm your resume information is accurate.")
    if not load_resume(body.resumeId):
        raise HTTPException(404, "Resume not found. Upload again from home.")
    if not body.applications:
        raise HTTPException(400, "Add at least one application on the tracker first.")

    try:
        apps = [a.model_dump() for a in body.applications]
        return await run_outreach_agent(body.resumeId, apps)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    except Exception as e:
        raise HTTPException(500, str(e)) from e
