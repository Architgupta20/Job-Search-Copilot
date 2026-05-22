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
  const jobUrl = body.jobUrl as string | undefined;
  const jobTitle = body.jobTitle as string | undefined;
  const snippet = body.snippet as string | null | undefined;

  if (!resumeId) {
    return NextResponse.json(
      { error: "Upload a resume on home first." },
      { status: 400 },
    );
  }
  if (!jobUrl || !jobTitle) {
    return NextResponse.json(
      { error: "jobUrl and jobTitle are required." },
      { status: 400 },
    );
  }

  if (!(await pythonApiAvailable())) {
    return NextResponse.json({ error: AGENTS_HINT }, { status: 503 });
  }

  const proxied = await proxyJsonPost("/api/company/job/tailor", {
    resumeId,
    jobUrl,
    jobTitle,
    snippet: snippet ?? null,
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
