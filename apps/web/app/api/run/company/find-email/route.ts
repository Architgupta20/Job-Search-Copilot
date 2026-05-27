import { NextResponse } from "next/server";
import {
  jsonFromProxy,
  proxyJsonPost,
  pythonApiAvailable,
} from "@/lib/python-api";

export const runtime = "nodejs";

const AGENTS_HINT =
  "Start both servers: npm run dev (from repo root, with conda env job-copilot)";

export async function POST(request: Request) {
  const body = await request.json();

  const personName = (body.personName as string | undefined)?.trim();
  const companyDomain = (body.companyDomain as string | undefined)?.trim();

  if (!personName || !companyDomain) {
    return NextResponse.json(
      { error: "personName and companyDomain are required." },
      { status: 400 },
    );
  }

  if (!(await pythonApiAvailable())) {
    return NextResponse.json({ error: AGENTS_HINT }, { status: 503 });
  }

  const proxied = await proxyJsonPost("/api/company/find-email", {
    personName,
    companyDomain,
    companyName: (body.companyName as string | undefined)?.trim() || null,
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
