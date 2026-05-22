import { NextResponse } from "next/server";
import {
  jsonFromProxy,
  proxyFormPost,
  pythonApiAvailable,
} from "@/lib/python-api";

export const runtime = "nodejs";

const AGENTS_HINT =
  "Start Python agents: cd agents && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000";

export async function POST(request: Request) {
  if (!(await pythonApiAvailable())) {
    return NextResponse.json({ error: AGENTS_HINT }, { status: 503 });
  }

  const formData = await request.formData();
  const proxied = await proxyFormPost("/api/resume/upload", formData);
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
