import { NextResponse } from "next/server";
import { runCompanySearch } from "@/lib/company/run";
import { loadResume } from "@/lib/resume/load";

export const runtime = "nodejs";
export const maxDuration = 60;

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const resumeId = body.resumeId as string | undefined;
    const companyName = body.companyName as string | undefined;
    const targetRoles = body.targetRoles as string[] | undefined;

    if (!resumeId) {
      return NextResponse.json(
        { error: "resumeId is required. Upload a resume first." },
        { status: 400 },
      );
    }

    if (!companyName?.trim()) {
      return NextResponse.json(
        { error: "companyName is required." },
        { status: 400 },
      );
    }

    if (!targetRoles?.length) {
      return NextResponse.json(
        { error: "Select at least one target role." },
        { status: 400 },
      );
    }

    const resume = await loadResume(resumeId);
    if (!resume) {
      return NextResponse.json(
        { error: "Resume not found. Upload again from home." },
        { status: 404 },
      );
    }

    const result = await runCompanySearch({
      companyName: companyName.trim(),
      targetRoles,
    });

    return NextResponse.json(result);
  } catch (err) {
    console.error("Company run failed:", err);
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Company search failed." },
      { status: 500 },
    );
  }
}
