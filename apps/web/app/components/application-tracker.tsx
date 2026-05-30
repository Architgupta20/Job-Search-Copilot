"use client";

import Link from "next/link";
import { FormEvent, useMemo, useState } from "react";
import {
  buildCompanyOutreachUrl,
  fetchColdOutreachDraft,
  type ColdOutreachDraft,
} from "@/lib/outreach/draft";
import { buildInterviewPrepUrl } from "@/lib/interview-prep/url";
import { getResumeSession } from "@/lib/resume/session";
import {
  APPLICATION_STATUSES,
  STATUS_LABELS,
  type ApplicationEntry,
  type ApplicationStatus,
} from "@/lib/tracker/types";
import {
  addApplication,
  deleteApplication,
  markOutreachSent,
  updateApplication,
} from "@/lib/tracker/storage";
import {
  buildFollowUpDraft,
  daysSince,
  DEFAULT_FOLLOW_UP_DAYS,
  followUpSuggested,
  getOutreachSentAt,
  type FollowUpDraft,
} from "@/lib/tracker/follow-up";
import { downloadApplicationsCsv } from "@/lib/tracker/export-csv";
import { useApplications } from "@/lib/tracker/use-applications";
import {
  fieldInputClass,
  fieldLabelSmClass,
  fieldSelectClass,
  fieldTextareaClass,
} from "@/lib/ui/form-styles";

type Filter = "all" | ApplicationStatus;

const STATUS_STYLES: Record<ApplicationStatus, string> = {
  saved: "bg-zinc-100 text-zinc-800",
  applied: "bg-blue-100 text-blue-900",
  replied: "bg-violet-100 text-violet-900",
  interview: "bg-amber-100 text-amber-900",
  offer: "bg-emerald-100 text-emerald-900",
  rejected: "bg-red-100 text-red-800",
};

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return iso;
  }
}

function ApplicationRow({
  entry,
  onChanged,
}: {
  entry: ApplicationEntry;
  onChanged: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [notes, setNotes] = useState(entry.notes);
  const [followUpOpen, setFollowUpOpen] = useState(false);
  const [followUp, setFollowUp] = useState<FollowUpDraft | null>(null);
  const [outreachOpen, setOutreachOpen] = useState(false);
  const [outreachLoading, setOutreachLoading] = useState(false);
  const [outreachError, setOutreachError] = useState<string | null>(null);
  const [outreachDraft, setOutreachDraft] = useState<ColdOutreachDraft | null>(
    null,
  );

  const outreachUrl = buildCompanyOutreachUrl(entry);
  const interviewPrepUrl = buildInterviewPrepUrl(entry);

  const sentAt = getOutreachSentAt(entry);
  const due = followUpSuggested(entry);
  const canFollowUp =
    entry.status === "applied" ||
    entry.status === "saved" ||
    Boolean(sentAt);

  function onStatusChange(status: ApplicationStatus) {
    const patch: Parameters<typeof updateApplication>[1] = { status };
    if (status === "applied" && !entry.outreachSentAt) {
      patch.outreachSentAt = new Date().toISOString();
    }
    updateApplication(entry.id, patch);
    onChanged();
  }

  function openFollowUp() {
    setFollowUp(buildFollowUpDraft(entry));
    setFollowUpOpen(true);
  }

  async function openOutreachDraft() {
    if (outreachOpen) {
      setOutreachOpen(false);
      return;
    }
    setOutreachError(null);
    setOutreachLoading(true);
    setFollowUpOpen(false);
    try {
      const session = getResumeSession();
      const personName = entry.contactName?.trim() || "Hiring Manager";
      const personTitle = entry.role;
      const draft =
        outreachDraft ??
        (await fetchColdOutreachDraft({
          companyName: entry.company,
          personName,
          personTitle,
          matchedRole: entry.role,
          resumeId: session?.id ?? null,
        }));
      setOutreachDraft(draft);
      setOutreachOpen(true);
    } catch (e) {
      setOutreachError(
        e instanceof Error ? e.message : "Could not load outreach draft.",
      );
    } finally {
      setOutreachLoading(false);
    }
  }

  function onMarkEmailSent() {
    markOutreachSent(entry.id);
    onChanged();
  }

  function saveNotes() {
    updateApplication(entry.id, { notes });
    setEditing(false);
    onChanged();
  }

  function onDelete() {
    if (
      !window.confirm(
        `Remove ${entry.company} — ${entry.role} from your tracker?`,
      )
    ) {
      return;
    }
    deleteApplication(entry.id);
    onChanged();
  }

  return (
    <li className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="font-semibold text-zinc-900">{entry.company}</p>
          <p className="text-sm text-zinc-600">{entry.role}</p>
          {(entry.contactName || entry.contactEmail || entry.contactLinkedIn) && (
            <p className="mt-1 text-xs text-zinc-500">
              {entry.contactName && <span>{entry.contactName}</span>}
              {entry.contactEmail && (
                <span>
                  {entry.contactName ? " · " : ""}
                  {entry.contactEmail}
                </span>
              )}
              {entry.contactLinkedIn && (
                <>
                  {" "}
                  ·{" "}
                  <a
                    href={entry.contactLinkedIn}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-emerald-700 underline"
                  >
                    LinkedIn
                  </a>
                </>
              )}
            </p>
          )}
          <p className="mt-2 text-xs text-zinc-400">
            Updated {formatDate(entry.updatedAt)}
            {sentAt && (
              <>
                {" "}
                · First email logged {formatDate(sentAt)}
                {daysSince(sentAt) > 0 && ` (${daysSince(sentAt)}d ago)`}
              </>
            )}
          </p>
          {due && (
            <p className="mt-1 inline-block rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-900">
              Follow up suggested — no reply in {DEFAULT_FOLLOW_UP_DAYS}+ days
            </p>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={entry.status}
            onChange={(e) =>
              onStatusChange(e.target.value as ApplicationStatus)
            }
            className={`rounded-lg border border-zinc-200 px-2 py-1 text-xs font-semibold text-zinc-900 ${STATUS_STYLES[entry.status]}`}
            aria-label={`Status for ${entry.company}`}
          >
            {APPLICATION_STATUSES.map((s) => (
              <option key={s} value={s}>
                {STATUS_LABELS[s]}
              </option>
            ))}
          </select>
          {!sentAt && (entry.status === "saved" || entry.status === "applied") && (
            <button
              type="button"
              onClick={onMarkEmailSent}
              className="rounded-lg border border-blue-200 bg-blue-50 px-2 py-1 text-xs font-medium text-blue-900 hover:bg-blue-100"
            >
              Log email sent
            </button>
          )}
          <button
            type="button"
            onClick={openOutreachDraft}
            disabled={outreachLoading}
            className="rounded-lg border border-emerald-300 bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-900 hover:bg-emerald-100 disabled:opacity-60"
          >
            {outreachLoading
              ? "Loading…"
              : outreachOpen
                ? "Close outreach"
                : "Draft outreach"}
          </button>
          <Link
            href={outreachUrl}
            className="rounded-lg border border-zinc-300 bg-white px-2 py-1 text-xs font-medium text-zinc-800 hover:bg-zinc-50"
          >
            Open in Company →
          </Link>
          <Link
            href={interviewPrepUrl}
            className="rounded-lg border border-violet-300 bg-violet-50 px-2 py-1 text-xs font-semibold text-violet-900 hover:bg-violet-100"
          >
            Interview prep
          </Link>
          {canFollowUp && (
            <button
              type="button"
              onClick={() => {
                if (followUpOpen) setFollowUpOpen(false);
                else openFollowUp();
              }}
              className={`rounded-lg border px-2 py-1 text-xs font-semibold ${
                due
                  ? "border-amber-400 bg-amber-50 text-amber-950 hover:bg-amber-100"
                  : "border-zinc-300 bg-white text-zinc-900 hover:bg-zinc-50"
              }`}
            >
              {followUpOpen ? "Close follow-up" : "Draft follow-up"}
            </button>
          )}
          <button
            type="button"
            onClick={() => setEditing((v) => !v)}
            className="rounded-lg border border-zinc-300 px-2 py-1 text-xs font-medium text-zinc-700 hover:bg-zinc-50"
          >
            {editing ? "Cancel" : "Notes"}
          </button>
          <button
            type="button"
            onClick={onDelete}
            className="rounded-lg border border-red-200 px-2 py-1 text-xs font-medium text-red-700 hover:bg-red-50"
          >
            Remove
          </button>
        </div>
      </div>
      {outreachError && (
        <p className="mt-3 text-sm text-red-600" role="alert">
          {outreachError}
        </p>
      )}
      {outreachOpen && outreachDraft && (
        <div className="mt-4 rounded-xl border-2 border-emerald-200 bg-emerald-50/40 p-4">
          <p className="text-sm font-semibold text-zinc-900">Cold outreach draft</p>
          <p className="mt-1 text-xs text-zinc-600">
            From your resume only. Edit before sending
            {entry.contactName ? ` to ${entry.contactName}` : ""}.
          </p>
          <p className="mt-3 text-sm font-semibold text-zinc-900">
            Subject: {outreachDraft.subject}
          </p>
          <pre className="mt-2 whitespace-pre-wrap font-sans text-sm leading-relaxed text-zinc-900">
            {outreachDraft.body}
          </pre>
          <p className="mt-4 text-xs font-semibold text-[#0A66C2]">LinkedIn</p>
          <pre className="mt-1 whitespace-pre-wrap font-sans text-sm text-zinc-900">
            {outreachDraft.linkedInMessage}
          </pre>
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              type="button"
              className="rounded-lg bg-zinc-900 px-3 py-2 text-xs font-semibold text-white hover:bg-zinc-700"
              onClick={() =>
                navigator.clipboard.writeText(
                  `Subject: ${outreachDraft.subject}\n\n${outreachDraft.body}`,
                )
              }
            >
              Copy email
            </button>
            <button
              type="button"
              className="rounded-lg bg-[#0A66C2] px-3 py-2 text-xs font-semibold text-white hover:bg-[#004182]"
              onClick={() =>
                navigator.clipboard.writeText(outreachDraft.linkedInMessage)
              }
            >
              Copy LinkedIn
            </button>
          </div>
        </div>
      )}
      {followUpOpen && followUp && (
        <div className="mt-4 rounded-xl border-2 border-amber-200 bg-amber-50/40 p-4">
          <p className="text-sm font-semibold text-zinc-900">Follow-up email</p>
          <p className="mt-1 text-xs text-zinc-600">
            Polite check-in after {followUp.daysSinceOutreach} day
            {followUp.daysSinceOutreach === 1 ? "" : "s"}. Edit before sending.
          </p>
          <p className="mt-3 text-sm font-semibold text-zinc-900">
            Subject: {followUp.subject}
          </p>
          <pre className="mt-2 whitespace-pre-wrap font-sans text-sm leading-relaxed text-zinc-900">
            {followUp.body}
          </pre>
          <p className="mt-4 text-xs font-semibold text-[#0A66C2]">
            LinkedIn (short)
          </p>
          <pre className="mt-1 whitespace-pre-wrap font-sans text-sm text-zinc-900">
            {followUp.linkedInMessage}
          </pre>
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              type="button"
              className="rounded-lg bg-zinc-900 px-3 py-2 text-xs font-semibold text-white hover:bg-zinc-700"
              onClick={() =>
                navigator.clipboard.writeText(
                  `Subject: ${followUp.subject}\n\n${followUp.body}`,
                )
              }
            >
              Copy email
            </button>
            <button
              type="button"
              className="rounded-lg bg-[#0A66C2] px-3 py-2 text-xs font-semibold text-white hover:bg-[#004182]"
              onClick={() =>
                navigator.clipboard.writeText(followUp.linkedInMessage)
              }
            >
              Copy LinkedIn
            </button>
          </div>
        </div>
      )}
      {editing && (
        <div className="mt-3 border-t border-zinc-100 pt-3">
          <label className={fieldLabelSmClass}>Notes</label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
            className={fieldTextareaClass}
            placeholder="Follow-up date, recruiter name, interview feedback…"
          />
          <button
            type="button"
            onClick={saveNotes}
            className="mt-2 rounded-lg bg-zinc-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-zinc-700"
          >
            Save notes
          </button>
        </div>
      )}
      {!editing && entry.notes && (
        <p className="mt-3 border-t border-zinc-100 pt-3 text-sm text-zinc-700 whitespace-pre-wrap">
          {entry.notes}
        </p>
      )}
    </li>
  );
}

export function ApplicationTracker() {
  const { entries, ready, refresh } = useApplications();
  const [filter, setFilter] = useState<Filter>("all");
  const [formError, setFormError] = useState<string | null>(null);

  const counts = useMemo(() => {
    const c: Record<string, number> = { all: entries.length };
    for (const s of APPLICATION_STATUSES) {
      c[s] = entries.filter((e) => e.status === s).length;
    }
    return c;
  }, [entries]);

  const filtered = useMemo(() => {
    if (filter === "all") return entries;
    return entries.filter((e) => e.status === filter);
  }, [entries, filter]);

  function onAdd(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setFormError(null);
    const form = new FormData(e.currentTarget);
    const company = String(form.get("company") ?? "").trim();
    const role = String(form.get("role") ?? "").trim();
    const contactName = String(form.get("contactName") ?? "").trim();
    const contactEmail = String(form.get("contactEmail") ?? "").trim();
    const contactLinkedIn = String(form.get("contactLinkedIn") ?? "").trim();
    const status = String(form.get("status") ?? "saved") as ApplicationStatus;
    const notes = String(form.get("notes") ?? "").trim();

    if (!company || !role) {
      setFormError("Company and role are required.");
      return;
    }

    addApplication({
      company,
      role,
      contactName: contactName || null,
      contactEmail: contactEmail || null,
      contactLinkedIn: contactLinkedIn || null,
      status,
      notes,
    });
    e.currentTarget.reset();
    refresh();
  }

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-semibold text-zinc-900">
          Application tracker
        </h1>
        <p className="mt-2 text-sm text-zinc-600">
          Track companies, roles, and outreach status. Log when you email someone,
          then use <strong>Draft follow-up</strong> after {DEFAULT_FOLLOW_UP_DAYS}{" "}
          days with no reply. Saved on this device only.
        </p>
      </div>

      <form
        onSubmit={onAdd}
        className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm"
      >
        <h2 className="text-sm font-semibold text-zinc-900">Add application</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <div>
            <label className={fieldLabelSmClass}>Company</label>
            <input
              name="company"
              required
              placeholder="e.g. Razorpay"
              className={fieldInputClass}
            />
          </div>
          <div>
            <label className={fieldLabelSmClass}>Role</label>
            <input
              name="role"
              required
              placeholder="e.g. AI Engineer"
              className={fieldInputClass}
            />
          </div>
          <div>
            <label className={fieldLabelSmClass}>Contact name (optional)</label>
            <input
              name="contactName"
              placeholder="Hiring manager"
              className={fieldInputClass}
            />
          </div>
          <div>
            <label className={fieldLabelSmClass}>Contact email (optional)</label>
            <input
              name="contactEmail"
              type="email"
              placeholder="name@company.com"
              className={fieldInputClass}
            />
          </div>
          <div className="sm:col-span-2">
            <label className={fieldLabelSmClass}>LinkedIn URL (optional)</label>
            <input
              name="contactLinkedIn"
              type="url"
              placeholder="https://linkedin.com/in/..."
              className={fieldInputClass}
            />
          </div>
          <div>
            <label className={fieldLabelSmClass}>Status</label>
            <select name="status" defaultValue="saved" className={fieldSelectClass}>
              {APPLICATION_STATUSES.map((s) => (
                <option key={s} value={s}>
                  {STATUS_LABELS[s]}
                </option>
              ))}
            </select>
          </div>
          <div className="sm:col-span-2">
            <label className={fieldLabelSmClass}>Notes (optional)</label>
            <textarea
              name="notes"
              rows={2}
              placeholder="Where you found the role, next follow-up…"
              className={fieldTextareaClass}
            />
          </div>
        </div>
        {formError && (
          <p className="mt-3 text-sm text-red-600" role="alert">
            {formError}
          </p>
        )}
        <button
          type="submit"
          className="mt-4 rounded-xl bg-emerald-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-800"
        >
          Add to tracker
        </button>
      </form>

      <section className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap gap-2">
            <FilterChip
              active={filter === "all"}
              label={`All (${counts.all ?? 0})`}
              onClick={() => setFilter("all")}
            />
            {APPLICATION_STATUSES.map((s) => (
              <FilterChip
                key={s}
                active={filter === s}
                label={`${STATUS_LABELS[s]} (${counts[s] ?? 0})`}
                onClick={() => setFilter(s)}
              />
            ))}
          </div>
          {entries.length > 0 && (
            <button
              type="button"
              onClick={() => downloadApplicationsCsv(entries)}
              className="rounded-lg border border-zinc-300 bg-white px-3 py-1.5 text-xs font-semibold text-zinc-900 hover:bg-zinc-50"
            >
              Download CSV
            </button>
          )}
        </div>

        {!ready ? (
          <p className="text-sm text-zinc-500">Loading…</p>
        ) : filtered.length === 0 ? (
          <p className="rounded-xl border border-dashed border-zinc-300 bg-white px-4 py-8 text-center text-sm text-zinc-500">
            {entries.length === 0
              ? "No applications yet. Add one above or save a contact from the Company page."
              : "No applications with this status."}
          </p>
        ) : (
          <ul className="space-y-3">
            {filtered.map((entry) => (
              <ApplicationRow
                key={entry.id}
                entry={entry}
                onChanged={refresh}
              />
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

function FilterChip({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full px-3 py-1 text-xs font-medium transition ${
        active
          ? "bg-zinc-900 text-white"
          : "border border-zinc-300 bg-white text-zinc-700 hover:bg-zinc-50"
      }`}
    >
      {label}
    </button>
  );
}
