/** Proxy to Python FastAPI agents when the service is running. */

const DEFAULT_BASE = "http://127.0.0.1:8000";

export function getPythonApiBase(): string {
  return (
    process.env.PYTHON_API_URL?.trim() ||
    process.env.AGENTS_API_URL?.trim() ||
    DEFAULT_BASE
  );
}

export async function pythonApiAvailable(
  base = getPythonApiBase(),
): Promise<boolean> {
  try {
    const res = await fetch(`${base}/health`, {
      signal: AbortSignal.timeout(2000),
      cache: "no-store",
    });
    return res.ok;
  } catch {
    return false;
  }
}

export async function proxyJsonPost(
  path: string,
  body: unknown,
): Promise<Response | null> {
  const base = getPythonApiBase();
  try {
    return await fetch(`${base}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
    });
  } catch {
    return null;
  }
}

export async function proxyFormPost(
  path: string,
  formData: FormData,
): Promise<Response | null> {
  const base = getPythonApiBase();
  try {
    return await fetch(`${base}${path}`, {
      method: "POST",
      body: formData,
      cache: "no-store",
    });
  } catch {
    return null;
  }
}

export async function proxyGet(path: string): Promise<Response | null> {
  const base = getPythonApiBase();
  try {
    return await fetch(`${base}${path}`, { cache: "no-store" });
  } catch {
    return null;
  }
}

function formatProxyError(data: unknown): string | undefined {
  if (!data || typeof data !== "object") return undefined;
  const obj = data as Record<string, unknown>;
  if (typeof obj.error === "string") return obj.error;
  const detail = obj.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d) =>
        typeof d === "object" && d && "msg" in d
          ? String((d as { msg: unknown }).msg)
          : String(d),
      )
      .join("; ");
  }
  return undefined;
}

export async function jsonFromProxy(
  res: Response,
): Promise<{ data: unknown; status: number }> {
  const raw = await res.json().catch(() => null);
  const message =
    formatProxyError(raw) ?? res.statusText ?? "Request failed.";
  const data =
    raw && typeof raw === "object"
      ? { ...(raw as object), error: message }
      : { error: message };
  return { data, status: res.status };
}
