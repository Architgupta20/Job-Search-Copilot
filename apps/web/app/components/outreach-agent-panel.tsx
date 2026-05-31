"use client";

import Link from "next/link";
import { useState } from "react";
import type { ApplicationEntry } from "@/lib/tracker/types";
import {
  trackerToAgentPayload,
  type OutreachAgentResult,
  type OutreachPlanItem,
} from "@/lib/outreach-agent/types";
import { getResumeSession } from "@/lib/resume/session";
import { checkboxClass } from "@/lib/ui/form-styles";

const PRIORITY_STYLES: Record<string, string> = {
  high: "border-red-200 bg-red-50 text-red-950",
  medium: "border-amber-200 bg-amber-50 text-amber-950",
  low: "border-zinc-200 bg-zinc-50 text-zinc-800",
};

function PlanCard({ plan }: { plan: OutreachPlanItem }) {
  const [open, setOpen] = useState(plan.priority === "high");
  const draft = plan.draft;
  const hasDraft = Boolean(draft?.body);

  return (
    <li
      className={`rounded-xl border p-4 ${PRIORITY_STYLES[plan.priority] ?? PRIORITY_STYLES.low}`}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="text-sm font-semibold">
            {plan.companyName} — {plan.roleTitle}
          </p>
          <p className="mt-1 text-xs opacity-90">
            {plan.actionLabel} · {plan.reason}
          </p>
        </div>
        <span className="rounded-full bg-white/80 px-2 py-0.5 text-xs font-semibold uppercase">
          {plan.priority}
        </span>
      </div>

      {plan.links.interviewPrep && (
        <Link
          href={plan.links.interviewPrep}
          className="mt-3 inline-block text-sm font-semibold text-violet-900 underline hover:no-underline"
        >
          Open interview prep →
        </Link>
      )}

      {hasDraft && (
        <div className="mt-3">
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            className="text-xs font-semibold underline hover:no-underline"
          >
            {open ? "Hide draft" : "Show draft"}
          </button>
          {open && (
            <div className="mt-3 rounded-lg border border-white/60 bg-white/90 p-3 text-sm text-zinc-900">
              {draft?.subject && (
                <p className="font-semibold">Subject: {draft.subject}</p>
              )}
              <pre className="mt-2 whitespace-pre-wrap font-sans leading-relaxed">
                {draft?.body}
              </pre>
              {draft?.linkedInMessage && (
                <>
                  <p className="mt-3 text-xs font-semibold text-[#0A66C2]">
                    LinkedIn
                  </p>
                  <pre className="mt-1 whitespace-pre-wrap font-sans text-sm">
                    {draft.linkedInMessage}
                  </pre>
                </>
              )}
              <button
                type="button"
                className="mt-3 rounded-lg bg-zinc-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-zinc-700"
                onClick={() =>
                  navigator.clipboard.writeText(
                    draft?.subject
                      ? `Subject: ${draft.subject}\n\n${draft.body}`
                      : draft?.body ?? "",
                  )
                }
              >
                Copy email
              </button>
            </div>
          )}
        </div>
      )}
    </li>
  );
}

export function OutreachAgentPanel({
  entries,
}: {
  entries: ApplicationEntry[];
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<OutreachAgentResult | null>(null);
  const [confirmed, setConfirmed] = useState(false);

  async function runAgent() {
    setError(null);
    setResult(null);

    const session = getResumeSession();
    if (!session) {
      setError("Upload a resume on the home page first.");
      return;
    }
    if (!entries.length) {
      setError("Add applications to the tracker first.");
      return;
    }
    if (!confirmed) {
      setError("Confirm your resume is accurate before running the agent.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch("/api/run/outreach-agent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resumeId: session.id,
          applications: trackerToAgentPayload(entries),
          confirmed: true,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Outreach agent failed.");
      setResult(data as OutreachAgentResult);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Outreach agent failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-2xl border border-indigo-200 bg-indigo-50/50 p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-zinc-900">Outreach agent</h2>
      <p className="mt-1 text-sm text-zinc-600">
        Scans your tracker and suggests the next action per application — initial
        outreach, follow-up, thank-you, or interview prep — with resume-backed
        drafts when possible.
      </p>

      <label className="mt-4 flex items-start gap-2 text-sm text-zinc-800">
        <input
          type="checkbox"
          checked={confirmed}
          onChange={(e) => setConfirmed(e.target.checked)}
          className={`${checkboxClass} mt-0.5`}
        />
        I confirm my resume only contains accurate information.
      </label>

      <button
        type="button"
        disabled={loading || !entries.length}
        onClick={runAgent}
        className="mt-4 rounded-xl bg-indigo-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-indigo-800 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {loading ? "Analyzing tracker…" : "Run outreach agent"}
      </button>

      {error && (
        <p className="mt-3 text-sm text-red-600" role="alert">
          {error}
        </p>
      )}

      {result && (
        <div className="mt-6 space-y-4">
          <p className="text-sm text-indigo-950">
            <strong>{result.summary.highPriority}</strong> high-priority action
            {result.summary.highPriority === 1 ? "" : "s"} of{" "}
            {result.summary.total} applications.
          </p>
          {result.warnings.map((w) => (
            <p key={w} className="text-xs text-indigo-900/80">
              {w}
            </p>
          ))}
          <ul className="space-y-3">
            {result.plans.map((plan) => (
              <PlanCard key={plan.applicationId} plan={plan} />
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
