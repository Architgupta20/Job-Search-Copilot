import { NextResponse } from "next/server";
import {
  jsonFromProxy,
  proxyGet,
  pythonApiAvailable,
} from "@/lib/python-api";
import type { ServiceConfig } from "@/lib/config/types";

export const runtime = "nodejs";

const AGENTS_HINT =
  "Start agents: npm run dev (from repo root, conda env job-copilot)";

const FALLBACK: ServiceConfig = {
  llm: { provider: "unknown", configured: false },
  serpapi: { configured: false, disabled: false, available: false },
  hunter: { configured: false },
};

export async function GET() {
  if (!(await pythonApiAvailable())) {
    return NextResponse.json(
      { ...FALLBACK, error: AGENTS_HINT },
      { status: 503 },
    );
  }

  const res = await proxyGet("/health/services");
  if (!res) {
    return NextResponse.json(
      { ...FALLBACK, error: AGENTS_HINT },
      { status: 503 },
    );
  }

  const { data, status } = await jsonFromProxy(res);
  if (!res.ok) {
    return NextResponse.json(
      { ...FALLBACK, error: (data as { error?: string }).error },
      { status },
    );
  }

  return NextResponse.json(data as ServiceConfig);
}
