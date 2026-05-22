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
  const [showDrafts, setShowDrafts] = useState(false);
  const [showHints, setShowHints] = useState(false);

  const needsContactHelp =
    !person.email && person.emailConfidence === "not_found";

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
      setShowDrafts(true);
      if (data.warning) setError(data.warning);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Draft failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <li className="py-4 first:pt-0">
      <p className="font-medium text-zinc-900">{person.name}</p>
      <p className="text-sm text-zinc-600">{person.title}</p>
      {person.matchedRole && (
        <p className="mt-1 text-xs text-emerald-800">
          Matched search: {person.matchedRole} (or equivalent title)
        </p>
      )}

      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm text-zinc-700">
        <span>
          Email: {person.email ?? "—"}{" "}
          <ConfidenceBadge value={person.emailConfidence} />
        </span>
        <span>
          Phone: {person.phone ?? "—"}{" "}
          <ConfidenceBadge value={person.phoneConfidence} />
        </span>
      </div>

      {needsContactHelp && person.contactHints && person.contactHints.length > 0 && (
        <div className="mt-2">
          <button
            type="button"
            onClick={() => setShowHints((v) => !v)}
            className="text-xs font-medium text-emerald-800 underline"
          >
            {showHints ? "Hide" : "Where to find email / phone"}
          </button>
          {showHints && (
            <ul className="mt-2 list-inside list-disc space-y-1 rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 text-xs text-zinc-600">
              {person.contactHints.map((hint) => (
                <li key={hint}>{hint}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      <div className="mt-3 flex flex-wrap gap-2">
        {person.linkedinUrl && (
          <a
            href={person.linkedinUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-emerald-700 underline"
          >
            LinkedIn
          </a>
        )}
        <button
          type="button"
          disabled={loading}
          onClick={draftOutreach}
          className="rounded-lg border border-zinc-300 px-2 py-1 text-xs font-medium hover:bg-zinc-50 disabled:opacity-50"
        >
          {loading ? "Drafting…" : "Draft email + LinkedIn"}
        </button>
        {draft && (
          <button
            type="button"
            onClick={() => setShowDrafts((v) => !v)}
            className="rounded-lg border border-emerald-300 px-2 py-1 text-xs text-emerald-800 hover:bg-emerald-50"
          >
            {showDrafts ? "Hide drafts" : "Show drafts"}
          </button>
        )}
      </div>

      {error && (
        <p
          className={`mt-2 text-sm ${draft ? "text-amber-800" : "text-red-600"}`}
          role="alert"
        >
          {error}
        </p>
      )}

      {showDrafts && draft && (
        <div className="mt-3 space-y-4">
          <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-3 text-sm">
            <p className="font-semibold text-zinc-900">Cold email</p>
            <p className="mt-2 font-medium text-zinc-800">
              Subject: {draft.subject}
            </p>
            <pre className="mt-2 whitespace-pre-wrap font-sans text-zinc-700">
              {draft.body}
            </pre>
            <button
              type="button"
              className="mt-2 text-xs font-medium underline"
              onClick={() =>
                navigator.clipboard.writeText(
                  `Subject: ${draft.subject}\n\n${draft.body}`,
                )
              }
            >
              Copy full email
            </button>
          </div>

          <div className="rounded-lg border border-blue-200 bg-blue-50/60 p-3 text-sm">
            <p className="font-semibold text-zinc-900">LinkedIn message</p>
            <p className="mt-1 text-xs text-zinc-500">
              Paste into connection note or InMail ({draft.linkedInMessage.length}{" "}
              chars)
            </p>
            <pre className="mt-2 whitespace-pre-wrap font-sans text-zinc-700">
              {draft.linkedInMessage}
            </pre>
            <button
              type="button"
              className="mt-2 text-xs font-medium underline"
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
