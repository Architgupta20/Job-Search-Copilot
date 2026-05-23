"use client";

import { useState } from "react";
import type { ColdOutreachDraft, PersonResult } from "@/lib/company/types";
import { getResumeSession } from "@/lib/resume/session";

function ConfidenceBadge({ value }: { value: string }) {
  const styles: Record<string, string> = {
    verified: "bg-emerald-100 text-emerald-800",
    likely: "bg-amber-100 text-amber-900",
    not_found: "bg-zinc-100 text-zinc-600",
  };
  return (
    <span
      className={`rounded px-1.5 py-0.5 text-xs font-medium ${styles[value] ?? styles.not_found}`}
    >
      {value.replace("_", " ")}
    </span>
  );
}

export function PersonCard({
  person,
  companyName,
}: {
  person: PersonResult;
  companyName: string;
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState<ColdOutreachDraft | null>(null);
  const [showResearch, setShowResearch] = useState(false);

  const research = person.contactResearch;
  const hasEmail = Boolean(person.email);

  async function draftOutreach() {
    const session = getResumeSession();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/run/company/cold-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          companyName,
          personName: person.name,
          personTitle: person.title,
          matchedRole: person.matchedRole,
          resumeId: session?.id ?? null,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Draft failed.");
      setDraft({
        subject: data.subject,
        body: data.body,
        linkedInMessage: data.linkedInMessage ?? "",
        warning: data.warning,
        source: data.source,
      });
      if (data.warning) setError(data.warning);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Draft failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <li className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
      <p className="font-medium text-zinc-900">{person.name}</p>
      <p className="text-sm text-zinc-600">{person.title}</p>
      {person.matchedRole && (
        <p className="mt-1 text-xs text-emerald-800">
          Matched: {person.matchedRole} (or equivalent)
        </p>
      )}

      <div className="mt-3 rounded-lg border border-violet-200 bg-violet-50/50 p-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-violet-900">
          Contact research
        </p>
        <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm text-zinc-800">
          <span>
            Email: {person.email ?? "Not found"}{" "}
            <ConfidenceBadge value={person.emailConfidence} />
          </span>
          <span>
            Phone: {person.phone ?? "Not found"}{" "}
            <ConfidenceBadge value={person.phoneConfidence} />
          </span>
        </div>
        {research && research.sourcesChecked.length > 0 && (
          <p className="mt-2 text-xs text-zinc-600">
            Checked: {research.sourcesChecked.join(" · ")}
          </p>
        )}
        {research && research.candidates.length > 0 && (
          <button
            type="button"
            onClick={() => setShowResearch((v) => !v)}
            className="mt-2 text-xs font-medium text-violet-800 underline"
          >
            {showResearch ? "Hide" : "Show"} all findings (
            {research.candidates.length})
          </button>
        )}
        {showResearch && research?.candidates && (
          <ul className="mt-2 space-y-1 text-xs text-zinc-700">
            {research.candidates.map((c, i) => (
              <li
                key={`${c.source}-${i}`}
                className="rounded border border-violet-100 bg-white px-2 py-1"
              >
                {c.email && <span className="font-medium">{c.email}</span>}
                {c.phone && !c.email && (
                  <span className="font-medium">{c.phone}</span>
                )}
                {!c.email && !c.phone && c.detail && (
                  <span className="text-zinc-500">{c.detail}</span>
                )}
                <span className="text-zinc-500"> — {c.source}</span>
              </li>
            ))}
          </ul>
        )}
        {!hasEmail && person.contactHints && person.contactHints.length > 0 && (
          <ul className="mt-2 list-inside list-disc text-xs text-zinc-600">
            {person.contactHints.slice(0, 4).map((h) => (
              <li key={h}>{h}</li>
            ))}
          </ul>
        )}
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {person.linkedinUrl && (
          <a
            href={person.linkedinUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-emerald-700 underline"
          >
            Open LinkedIn
          </a>
        )}
        <button
          type="button"
          disabled={loading}
          onClick={draftOutreach}
          className="rounded-lg bg-zinc-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-zinc-700 disabled:opacity-50"
        >
          {loading ? "Drafting…" : "Draft email + LinkedIn"}
        </button>
      </div>

      {error && (
        <p
          className={`mt-2 text-sm ${draft ? "text-amber-800" : "text-red-600"}`}
          role="alert"
        >
          {error}
        </p>
      )}

      {draft && (
        <div className="mt-4 grid gap-4 lg:grid-cols-2">
          <div className="flex flex-col rounded-xl border-2 border-zinc-300 bg-zinc-50 p-4 shadow-sm">
            <div className="mb-3 border-b border-zinc-200 pb-2">
              <p className="text-sm font-bold text-zinc-900">Cold email</p>
              <p className="text-xs text-zinc-500">
                Copy into Gmail / Outlook — full format with subject
              </p>
            </div>
            <p className="text-sm font-semibold text-zinc-800">
              Subject: {draft.subject}
            </p>
            <pre className="mt-3 flex-1 whitespace-pre-wrap font-sans text-sm leading-relaxed text-zinc-700">
              {draft.body}
            </pre>
            <button
              type="button"
              className="mt-3 w-full rounded-lg border border-zinc-400 bg-white py-2 text-xs font-semibold hover:bg-zinc-100"
              onClick={() =>
                navigator.clipboard.writeText(
                  `Subject: ${draft.subject}\n\n${draft.body}`,
                )
              }
            >
              Copy email
            </button>
          </div>

          <div className="flex flex-col rounded-xl border-2 border-[#0A66C2] bg-[#0A66C2]/5 p-4 shadow-sm">
            <div className="mb-3 border-b border-[#0A66C2]/30 pb-2">
              <p className="text-sm font-bold text-[#0A66C2]">LinkedIn message</p>
              <p className="text-xs text-zinc-600">
                Connection note or InMail — {draft.linkedInMessage.length} / 300
                chars
              </p>
            </div>
            <pre className="flex-1 whitespace-pre-wrap font-sans text-sm leading-relaxed text-zinc-800">
              {draft.linkedInMessage}
            </pre>
            <button
              type="button"
              className="mt-3 w-full rounded-lg border border-[#0A66C2] bg-white py-2 text-xs font-semibold text-[#0A66C2] hover:bg-[#0A66C2]/10"
              onClick={() =>
                navigator.clipboard.writeText(draft.linkedInMessage)
              }
            >
              Copy LinkedIn message
            </button>
          </div>
        </div>
      )}
    </li>
  );
}
