import { NextResponse } from "next/server";
import {
  jsonFromProxy,
  proxyJsonPost,
  pythonApiAvailable,
} from "@/lib/python-api";

export const runtime = "nodejs";
export const maxDuration = 120;

const AGENTS_HINT =
  "Start both servers: npm run dev (from repo root, with conda env job-copilot)";

export async function POST(request: Request) {
  const body = await request.json();
  const resumeId = body.resumeId as string | undefined;
  const companyName = body.companyName as string | undefined;
  const targetRoles = body.targetRoles as string[] | undefined;
  const careersUrlOverride = body.careersUrlOverride as string | undefined;
  const locationCountry = body.locationCountry as string | undefined;
  const locationCity = body.locationCity as string | undefined;

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

  if (!(await pythonApiAvailable())) {
    return NextResponse.json({ error: AGENTS_HINT }, { status: 503 });
  }

  const proxied = await proxyJsonPost("/api/company/run", {
    resumeId: resumeId ?? null,
    companyName: companyName.trim(),
    targetRoles,
    careersUrlOverride: careersUrlOverride?.trim() || null,
    locationCountry: locationCountry?.trim() || null,
    locationCity: locationCity?.trim() || null,
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
