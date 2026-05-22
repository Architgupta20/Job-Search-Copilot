import { NextResponse } from "next/server";
import { loadResume } from "@/lib/resume/load";

export const runtime = "nodejs";

export async function GET(
  _request: Request,
  context: { params: Promise<{ id: string }> },
) {
  const { id } = await context.params;
  const record = await loadResume(id);

  if (!record) {
    return NextResponse.json({ error: "Resume not found." }, { status: 404 });
  }

  return NextResponse.json({
    id: record.id,
    fileName: record.fileName,
    uploadedAt: record.uploadedAt,
    contact: record.parsedFacts.contact,
    claimCount: record.parsedFacts.allowedClaims.length,
  });
}
