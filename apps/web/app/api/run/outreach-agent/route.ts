import { NextResponse } from "next/server";
import {
  jsonFromProxy,
  proxyJsonPost,
  pythonApiAvailable,
} from "@/lib/python-api";

export const runtime = "nodejs";
export const maxDuration = 120;

const AGENTS_HINT =
  "Start Python agents: conda activate job-copilot && npm run dev:lite";

export async function POST(request: Request) {
  const body = await request.json();

  if (!(await pythonApiAvailable())) {
    return NextResponse.json({ error: AGENTS_HINT }, { status: 503 });
  }

  const proxied = await proxyJsonPost("/api/outreach-agent/run", body);
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
