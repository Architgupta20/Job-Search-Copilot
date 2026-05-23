"use client";

import { useEffect, useState } from "react";
import type { ServiceConfig } from "@/lib/config/types";

export function ServiceStatusBanner() {
  const [config, setConfig] = useState<ServiceConfig | null>(null);
  const [agentsDown, setAgentsDown] = useState(false);

  useEffect(() => {
    fetch("/api/config")
      .then(async (res) => {
        const data = await res.json();
        if (!res.ok) {
          setAgentsDown(true);
          return;
        }
        setConfig(data as ServiceConfig);
      })
      .catch(() => setAgentsDown(true));
  }, []);

  if (agentsDown) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-900">
        Python agents are not running. Start with{" "}
        <code className="rounded bg-red-100 px-1">npm run dev</code> from the
        repo root.
      </div>
    );
  }

  if (!config) return null;

  const messages: string[] = [];

  if (!config.serpapi.available) {
    if (!config.serpapi.configured) {
      messages.push(
        "SerpAPI key missing — automated LinkedIn people search will not run. Use Manual outreach below, or add SERPAPI_API_KEY to apps/web/.env.",
      );
    } else if (config.serpapi.disabled) {
      messages.push(
        "SerpAPI is paused (SERPAPI_DISABLED=true). Use Manual outreach to add LinkedIn contacts and draft email / LinkedIn messages.",
      );
    }
  }

  if (!config.llm.configured) {
    messages.push(
      "LLM not configured — JD tailoring may fail. Set LLM_PROVIDER and API keys in apps/web/.env (Groq, Ollama, or OpenAI).",
    );
  }

  if (!config.hunter.configured) {
    messages.push(
      "Hunter.io not set — email discovery on automated search will be limited. You can still paste emails in Manual outreach.",
    );
  }

  if (messages.length === 0) return null;

  return (
    <ul className="space-y-2 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950">
      {messages.map((m) => (
        <li key={m}>• {m}</li>
      ))}
    </ul>
  );
}
