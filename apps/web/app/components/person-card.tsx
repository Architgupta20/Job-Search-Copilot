"use client";

import { useState } from "react";
import type { ColdOutreachDraft, PersonResult } from "@/lib/company/types";
import { getResumeSession } from "@/lib/resume/session";
import { addApplicationFromContact } from "@/lib/tracker/storage";

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
  companyDomain,
  showSaveToTracker = true,
}: {
  person: PersonResult;
  companyName: string;
  companyDomain?: string | null;
  /** False when parent already added this contact to the tracker. */
  showSaveToTracker?: boolean;
}) {
  const [loadingWhich, setLoadingWhich] = useState<"email" | "linkedin" | null>(
    null,
  );
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState<ColdOutreachDraft | null>(null);
  const [showResearch, setShowResearch] = useState(false);
  const [emailOpen, setEmailOpen] = useState(false);
  const [linkedInOpen, setLinkedInOpen] = useState(false);
  const [trackerMsg, setTrackerMsg] = useState<string | null>(null);
  const [findingEmail, setFindingEmail] = useState(false);
  const [foundEmail, setFoundEmail] = useState<{
    email: string | null;
    confidence: string;
    source: string | null;
    error?: string;
  } | null>(null);
  const isLoading = loadingWhich !== null;

  const research = person.contactResearch;
  const hasEmail = Boolean(person.email) || Boolean(foundEmail?.email);

  async function loadDraft(which: "email" | "linkedin") {
    if (draft) return draft;
    const session = getResumeSession();
    setLoadingWhich(which);
    setError(null);
    try {
      const res = await fetch("/api/run/company/cold-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          companyName,
          companyDomain: companyDomain ?? null,
          personName: person.name,
          personTitle: person.title,
          matchedRole: person.matchedRole,
          resumeId: session?.id ?? null,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Draft failed.");
      const next: ColdOutreachDraft = {
        subject: data.subject,
        body: data.body,
        linkedInMessage: data.linkedInMessage ?? "",
        companyAngle: data.companyAngle,
        warning: data.warning,
        source: data.source,
      };
      setDraft(next);
      if (data.warning && data.source !== "structured") setError(data.warning);
      return next;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Draft failed.");
      return null;
    } finally {
      setLoadingWhich(null);
    }
  }

  async function toggleEmail() {
    if (emailOpen) {
      setEmailOpen(false);
      return;
    }
    setLinkedInOpen(false);
    const d = draft ?? (await loadDraft("email"));
    if (d) setEmailOpen(true);
  }

  async function toggleLinkedIn() {
    if (linkedInOpen) {
      setLinkedInOpen(false);
      return;
    }
    setEmailOpen(false);
    const d = draft ?? (await loadDraft("linkedin"));
    if (d) setLinkedInOpen(true);
  }

  async function findEmail() {
    if (!companyDomain) return;
    setFindingEmail(true);
    setFoundEmail(null);
    try {
      const res = await fetch("/api/run/company/find-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          personName: person.name,
          companyDomain,
          companyName,
        }),
      });
      const data = await res.json();
      setFoundEmail({
        email: data.email ?? null,
        confidence: data.confidence ?? "not_found",
        source: data.source ?? null,
        error: data.error ?? undefined,
      });
    } catch {
      setFoundEmail({ email: null, confidence: "not_found", source: null, error: "Request failed." });
    } finally {
      setFindingEmail(false);
    }
  }

  function saveToTracker() {
    const { duplicate } = addApplicationFromContact({
      company: companyName,
      role: person.matchedRole || person.title,
      contactName: person.name,
      contactLinkedIn: person.linkedinUrl,
      contactEmail: person.email,
      status: "saved",
    });
    setTrackerMsg(
      duplicate ? "Already in tracker." : "Saved to tracker — open Tracker in the menu.",
    );
    window.setTimeout(() => setTrackerMsg(null), 4000);
  }

  return (
    <article className="mb-5 rounded-xl border border-zinc-200 bg-white p-5 shadow-sm last:mb-0">
      <p className="font-medium text-zinc-900">{person.name}</p>
      <p className="text-sm text-zinc-600">{person.title}</p>
      {person.matchedRole && (
        <p className="mt-1 text-xs text-emerald-800">
          Matched: {person.matchedRole} · current employee
        </p>
      )}

      <div className="mt-4 rounded-lg border border-violet-200 bg-violet-50/50 p-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-zinc-900">
          Contact research
        </p>
        <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm text-zinc-800">
          <span>
            Email:{" "}
            {foundEmail?.email ?? person.email ?? "Not found"}{" "}
            <ConfidenceBadge
              value={
                foundEmail?.email
                  ? foundEmail.confidence
                  : person.emailConfidence
              }
            />
            {foundEmail?.source && (
              <span className="ml-1 text-xs text-zinc-500">
                via {foundEmail.source}
              </span>
            )}
          </span>
          <span>
            Phone: {person.phone ?? "Not found"}{" "}
            <ConfidenceBadge value={person.phoneConfidence} />
          </span>
        </div>
        {!person.email && !foundEmail?.email && companyDomain && (
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <button
              type="button"
              disabled={findingEmail}
              onClick={findEmail}
              className="rounded-lg border border-violet-300 bg-white px-2.5 py-1 text-xs font-semibold text-violet-900 hover:bg-violet-50 disabled:opacity-50"
            >
              {findingEmail ? "Searching Hunter…" : "Find email (Hunter)"}
            </button>
            {foundEmail?.error && (
              <p className="text-xs text-amber-800">{foundEmail.error}</p>
            )}
          </div>
        )}
        {!companyDomain && !person.email && (
          <p className="mt-2 text-xs text-zinc-500">
            Enter company domain above to enable Hunter email lookup.
          </p>
        )}
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

      <div className="mt-4 flex flex-wrap items-center gap-3">
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
          disabled={isLoading}
          onClick={toggleEmail}
          className={`rounded-lg border px-3 py-1.5 text-xs font-semibold disabled:opacity-50 ${
            emailOpen
              ? "border-zinc-900 bg-zinc-900 text-white"
              : "border-zinc-300 bg-white text-zinc-900 hover:bg-zinc-50"
          }`}
        >
          {loadingWhich === "email"
            ? "Loading…"
            : emailOpen
              ? "Close email"
              : "Draft email"}
        </button>
        <button
          type="button"
          disabled={isLoading}
          onClick={toggleLinkedIn}
          className={`rounded-lg border px-3 py-1.5 text-xs font-semibold disabled:opacity-50 ${
            linkedInOpen
              ? "border-[#0A66C2] bg-[#0A66C2] text-white"
              : "border-[#0A66C2] bg-white text-[#0A66C2] hover:bg-[#0A66C2]/10"
          }`}
        >
          {loadingWhich === "linkedin"
            ? "Loading…"
            : linkedInOpen
              ? "Close LinkedIn"
              : "Draft LinkedIn"}
        </button>
        {showSaveToTracker ? (
          <button
            type="button"
            onClick={saveToTracker}
            className="rounded-lg border border-emerald-600 px-3 py-1.5 text-xs font-semibold text-emerald-800 hover:bg-emerald-50"
          >
            Save to tracker
          </button>
        ) : (
          <span className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-900">
            In tracker
          </span>
        )}
      </div>

      {trackerMsg && (
        <p className="mt-2 text-xs font-medium text-emerald-800">{trackerMsg}</p>
      )}

      {error && (
        <p
          className={`mt-3 text-sm ${draft ? "text-amber-800" : "text-red-600"}`}
          role="alert"
        >
          {error}
        </p>
      )}

      {draft && emailOpen && (
        <div className="mt-5 rounded-xl border-2 border-zinc-300 bg-white p-4 shadow-md">
          <div className="mb-3 border-b border-zinc-200 pb-2">
            <p className="text-base font-bold text-zinc-900">Cold email</p>
            <p className="text-xs text-zinc-600">
              Gmail / Outlook — subject + full body
            </p>
          </div>
          <p className="text-sm font-semibold text-zinc-900">
            Subject: {draft.subject}
          </p>
          <pre className="mt-3 whitespace-pre-wrap font-sans text-sm leading-relaxed text-zinc-800">
            {draft.body}
          </pre>
          <button
            type="button"
            className="mt-3 w-full rounded-lg bg-zinc-900 py-2 text-xs font-semibold text-white hover:bg-zinc-700"
            onClick={() =>
              navigator.clipboard.writeText(
                `Subject: ${draft.subject}\n\n${draft.body}`,
              )
            }
          >
            Copy email
          </button>
        </div>
      )}

      {draft && linkedInOpen && (
        <div className="mt-5 rounded-xl border-2 border-[#0A66C2] bg-white p-4 shadow-md">
          <div className="mb-3 border-b border-[#0A66C2]/25 pb-2">
            <p className="text-base font-bold text-[#0A66C2]">LinkedIn message</p>
            <p className="text-xs text-zinc-600">
              Connection note or InMail — {draft.linkedInMessage.length} / 300 chars
            </p>
          </div>
          <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-zinc-900">
            {draft.linkedInMessage}
          </pre>
          <button
            type="button"
            className="mt-3 w-full rounded-lg bg-[#0A66C2] py-2 text-xs font-semibold text-white hover:bg-[#004182]"
            onClick={() =>
              navigator.clipboard.writeText(draft.linkedInMessage)
            }
          >
            Copy LinkedIn message
          </button>
        </div>
      )}
    </article>
  );
}
