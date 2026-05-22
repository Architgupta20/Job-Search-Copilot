import { NextResponse } from "next/server";
import { proxyGet, pythonApiAvailable } from "@/lib/python-api";

export const runtime = "nodejs";

const AGENTS_HINT =
  "Start Python agents: cd agents && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000";

export async function GET(
  request: Request,
  context: { params: Promise<{ runId: string }> },
) {
  const { runId } = await context.params;
  const format = new URL(request.url).searchParams.get("format") ?? "docx";

  if (!(await pythonApiAvailable())) {
    return NextResponse.json({ error: AGENTS_HINT }, { status: 503 });
  }

  const proxied = await proxyGet(
    `/api/jd/${runId}/download?format=${encodeURIComponent(format)}`,
  );
  if (!proxied?.ok) {
    const err = await proxied?.json().catch(() => ({ error: "Download failed." }));
    return NextResponse.json(err, { status: proxied?.status ?? 502 });
  }

  const headers = new Headers(proxied.headers);
  headers.set("X-Agent-Runtime", "python");
  return new NextResponse(proxied.body, {
    status: proxied.status,
    headers,
  });
}
