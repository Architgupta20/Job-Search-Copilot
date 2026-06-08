"use client";

import { useState } from "react";
import type { JobResult } from "@/lib/company/types";
import type { JobTailorResult } from "@/lib/company/types";
import { useResumeSession } from "@/lib/resume/session";

function atsColor(score: number) {
  if (score >= 70) return "bg-emerald-100 text-emerald-900 border-emerald-200";
  if (score >= 45) return "bg-amber-100 text-amber-900 border-amber-200";
  return "bg-zinc-100 text-zinc-700 border-zinc-200";
}

export function JobOpeningCard({ job }: { job: JobResult }) {
  const [tailoring, setTailoring] = useState(false);
  const [tailorError, setTailorError] = useState<string | null>(null);
  const [tailorResult, setTailorResult] = useState<JobTailorResult | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [draft, setDraft] = useState("");

  const { session } = useResumeSession();
  const hasAts = job.atsScorePercent != null;

  async function tailorForJob() {
    if (!session) {
      setTailorError("Upload a resume on the home page first.");
      return;
    }
    setTailoring(true);
    setTailorError(null);
    setTailorResult(null);
    try {
      const res = await fetch("/api/run/company/job/tailor", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resumeId: session.id,
          jobUrl: job.url,
          jobTitle: job.title,
          snippet: job.snippet,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Tailoring failed.");
      const result = data as JobTailorResult;
      setTailorResult(result);
      setDraft(result.tailoredText ?? "");
      setExpanded(true);
    } catch (e) {
      setTailorError(e instanceof Error ? e.message : "Tailoring failed.");
    } finally {
      setTailoring(false);
    }
  }

  return (
    <li className="rounded-lg border border-zinc-200 bg-white px-4 py-3 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="font-medium text-zinc-900">{job.title}</p>
          {job.matchedRole && (
            <p className="mt-0.5 text-xs text-emerald-700">{job.matchedRole}</p>
          )}
          {job.snippet && (
            <p className="mt-2 text-xs text-zinc-500 line-clamp-2">{job.snippet}</p>
          )}
        </div>
        {hasAts && (
          <div
            className={`shrink-0 rounded-full border px-3 py-1 text-center ${atsColor(job.atsScorePercent!)}`}
            title="ATS preview vs your uploaded resume"
          >
            <p className="text-xs font-medium uppercase tracking-wide">ATS</p>
            <p className="text-lg font-bold leading-tight">{job.atsScorePercent}%</p>
          </div>
        )}
        {!hasAts && (
          <p className="text-xs text-zinc-400">Upload resume for ATS</p>
        )}
      </div>

      {hasAts && job.atsBreakdown && (
        <p className="mt-2 text-xs text-zinc-500">
          {job.atsBreakdown.supportedCount} of {job.atsBreakdown.totalKeywords}{" "}
          keywords match your resume
        </p>
      )}

      <div className="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          disabled={!session || tailoring}
          onClick={tailorForJob}
          className="rounded-lg bg-zinc-900 px-3 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-50"
        >
          {tailoring ? "Tailoring…" : "Tailor my resume"}
        </button>
        <a
          href={job.url}
          target="_blank"
          rel="noopener noreferrer"
          className="rounded-lg border border-zinc-300 px-3 py-2 text-sm font-medium text-zinc-800 hover:bg-zinc-50"
        >
          Open posting →
        </a>
        {tailorResult && (
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            className="rounded-lg border border-emerald-300 px-3 py-2 text-sm text-emerald-800 hover:bg-emerald-50"
          >
            {expanded ? "Hide edits" : "Show edits"}
          </button>
        )}
      </div>

      {tailorError && (
        <p className="mt-2 text-sm text-red-600" role="alert">
          {tailorError}
        </p>
      )}

      {expanded && tailorResult && (
        <div className="mt-4 space-y-3 rounded-lg border border-emerald-100 bg-emerald-50/50 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm font-semibold text-zinc-900">
              Tailored for this role — ATS {tailorResult.atsScorePercent}%
            </p>
            <a
              href={`/api/run/jd/${tailorResult.runId}/download?format=docx`}
              download
              className="text-sm font-medium text-emerald-800 underline"
            >
              Download .docx
            </a>
          </div>
          <p className="text-xs text-zinc-600">
            Copy into your Word file — same as JD path. Facts only from your upload.
          </p>
          {(tailorResult.suggestedEdits?.length ?? 0) > 0 && (
            <ul className="max-h-40 space-y-2 overflow-y-auto text-sm text-zinc-700">
              {(tailorResult.suggestedEdits ?? []).slice(0, 5).map((edit, i) => (
                <li key={i} className="rounded border border-zinc-100 bg-white p-2">
                  <span className="font-medium text-emerald-800">{edit.section}:</span>{" "}
                  {edit.suggested}
                </li>
              ))}
            </ul>
          )}
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            rows={10}
            className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 font-mono text-sm"
          />
          <button
            type="button"
            onClick={() => navigator.clipboard.writeText(draft)}
            className="text-sm font-medium text-zinc-700 underline"
          >
            Copy draft
          </button>
        </div>
      )}
    </li>
  );
}
