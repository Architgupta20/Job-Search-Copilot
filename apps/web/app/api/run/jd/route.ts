import { NextResponse } from "next/server";
import {
  jsonFromProxy,
  proxyJsonPost,
  pythonApiAvailable,
} from "@/lib/python-api";

export const runtime = "nodejs";
export const maxDuration = 120;

const AGENTS_HINT =
  "Start Python agents: conda activate job-copilot && cd agents && uvicorn app.main:app --reload --port 8000";

export async function POST(request: Request) {
  const body = await request.json();
  const resumeId = body.resumeId as string | undefined;
  const jdText = body.jdText as string | undefined;
  const confirmed = body.confirmed as boolean | undefined;

  if (!resumeId) {
    return NextResponse.json(
      { error: "resumeId is required. Upload a resume first." },
      { status: 400 },
    );
  }

  if (!jdText?.trim() || jdText.trim().length < 80) {
    return NextResponse.json(
      { error: "Paste a job description (at least 80 characters)." },
      { status: 400 },
    );
  }

  if (!confirmed) {
    return NextResponse.json(
      { error: "Please confirm your resume information is accurate." },
      { status: 400 },
    );
  }

  if (!(await pythonApiAvailable())) {
    return NextResponse.json({ error: AGENTS_HINT }, { status: 503 });
  }

  const proxied = await proxyJsonPost("/api/jd/run", {
    resumeId,
    jdText: jdText.trim(),
    confirmed: true,
  });
  if (!proxied) {
    return NextResponse.json(
      { error: "Agents request failed." },
      { status: 502 },
    );
  }

  const { data, status } = await jsonFromProxy(proxied);
  return NextResponse.json(data, {
    status,
    headers: { "X-Agent-Runtime": "python" },
  });
}
