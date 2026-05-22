from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.company.run import run_company_search
from app.services.resume.parser import load_resume

router = APIRouter(prefix="/api/company", tags=["company"])


class CompanyRunBody(BaseModel):
    resumeId: str
    companyName: str
    targetRoles: list[str] = Field(min_length=1)


@router.post("/run")
async def company_run(body: CompanyRunBody):
    if not body.companyName.strip():
        raise HTTPException(400, "companyName is required.")
    if not body.targetRoles:
        raise HTTPException(400, "Select at least one target role.")

    if not load_resume(body.resumeId):
        raise HTTPException(404, "Resume not found. Upload again from home.")

    try:
        return await run_company_search(body.companyName.strip(), body.targetRoles)
    except Exception as e:
        raise HTTPException(500, str(e)) from e
