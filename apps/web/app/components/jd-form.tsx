"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import type { JDTailorResult } from "@/lib/jd/types";
import { getResumeSession } from "@/lib/resume/session";
import {
  checkboxClass,
  fieldLabelClass,
  fieldTextareaClass,
} from "@/lib/ui/form-styles";

function AtsScoreCard({ result }: { result: JDTailorResult }) {
  const ats = result.atsBreakdown;
  const score = ats?.scorePercent ?? result.atsScorePercent;
  const matched = ats?.matchedKeywords ?? result.keywordsUsed;
  const missing = ats?.missingKeywords ?? result.keywordsSkipped;

  return (
    <section className="rounded-2xl border-2 border-emerald-200 bg-emerald-50/50 p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h2 className="text-lg font-semibold text-zinc-900">ATS score</h2>
        <div className="text-right">
          <p className="text-4xl font-bold text-emerald-800">{score}%</p>
          <p className="text-xs text-zinc-600">
            {ats?.supportedCount ?? matched.length} of {ats?.totalKeywords ?? "—"}{" "}
            JD keywords supported by your resume
          </p>
        </div>
      </div>
      <div className="mt-4 h-3 overflow-hidden rounded-full bg-zinc-200">
        <div
          className="h-full rounded-full bg-emerald-600 transition-all"
          style={{ width: `${Math.min(100, score)}%` }}
        />
      </div>
      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <div>
          <h3 className="text-sm font-medium text-emerald-900">
            Matched (exact + related terms)
          </h3>
          <p className="mt-1 text-sm text-zinc-700">
            {matched.length > 0 ? matched.join(", ") : "—"}
          </p>
        </div>
        <div>
          <h3 className="text-sm font-medium text-amber-900">Missing (not in resume)</h3>
          <p className="mt-1 text-sm text-zinc-700">
            {missing.length > 0 ? missing.join(", ") : "—"}
          </p>
        </div>
      </div>
    </section>
  );
}

export function JDForm() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<JDTailorResult | null>(null);
  const [editableText, setEditableText] = useState("");
  const [copied, setCopied] = useState(false);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setResult(null);

    const session = getResumeSession();
    if (!session) {
      setError("Upload a resume on the home page first.");
      return;
    }

    const form = new FormData(e.currentTarget);
    const jdText = String(form.get("jd") ?? "").trim();
    const confirmed = form.get("confirm") === "on";

    if (!jdText || jdText.length < 80) {
      setError("Paste the full job description (at least 80 characters).");
      return;
    }

    if (!confirmed) {
      setError("Please confirm your resume is accurate.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch("/api/run/jd", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resumeId: session.id,
          jdText,
          confirmed: true,
        }),
      });
      const data = await res.json();
      const msg =
        data.error ??
        (typeof data.detail === "string" ? data.detail : null);
      if (!res.ok) throw new Error(msg ?? "Tailoring failed.");
      const typed = data as JDTailorResult;
      setResult(typed);
      setEditableText(typed.tailoredText ?? "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Tailoring failed.");
    } finally {
      setLoading(false);
    }
  }

  async function copyText() {
    await navigator.clipboard.writeText(editableText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  const warnings = Array.isArray(result?.warnings) ? result.warnings : [];
  const suggestedEdits = Array.isArray(result?.suggestedEdits)
    ? result.suggestedEdits
    : [];
  const changeSummary = Array.isArray(result?.changeSummary)
    ? result.changeSummary
    : [];

  return (
    <>
      <div>
        <Link href="/" className="text-sm text-zinc-500 hover:text-zinc-800">
          ← Back
        </Link>
        <h1 className="mt-4 text-2xl font-semibold text-zinc-900">
          Tailor to job description
        </h1>
        <p className="mt-2 text-zinc-600">
          Suggestions appear in the UI — copy into <strong>your own Word file</strong>.
          Download is optional plain text/DOCX (not your original formatting).
        </p>
      </div>

      <form
        onSubmit={onSubmit}
        className="space-y-6 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm"
      >
        <div>
          <label htmlFor="jd" className={fieldLabelClass}>
            Job description
          </label>
          <textarea
            id="jd"
            name="jd"
            rows={12}
            required
            placeholder="Paste the full job description here..."
            className={fieldTextareaClass}
          />
        </div>

        <label className="flex items-start gap-2 text-sm text-zinc-800">
          <input
            type="checkbox"
            name="confirm"
            required
            className={`${checkboxClass} mt-0.5`}
          />
          I confirm my resume only contains accurate information.
        </label>

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-xl bg-zinc-900 px-4 py-3 text-sm font-medium text-white transition hover:bg-zinc-700 disabled:cursor-wait disabled:opacity-70"
        >
          {loading ? "Analyzing JD & resume… (20–60s)" : "Get suggestions + ATS score"}
        </button>

        {error && (
          <p className="text-sm text-red-600" role="alert">
            {error}
          </p>
        )}
      </form>

      {result && (
        <div className="space-y-6">
          {warnings.map((w) => (
            <p
              key={w}
              className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900"
            >
              {w}
            </p>
          ))}

          <AtsScoreCard result={result} />

          {result.jdTitle && (
            <p className="text-sm text-zinc-600">
              Role: <strong>{result.jdTitle}</strong>
            </p>
          )}

          {suggestedEdits.length > 0 && (
            <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-zinc-900">
                Resume edits — {suggestedEdits.length} bullets to update
              </h2>
              <p className="mt-1 text-sm text-zinc-500">
                Each card shows which <strong>resume section</strong> the bullet came from, your current text, and the rewrite. Paste the green text into that section in Word.
              </p>
              <ol className="mt-4 space-y-5">
                {suggestedEdits.map((edit, i) => (
                  <li
                    key={`${edit.section}-${i}`}
                    className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm"
                  >
                    <div className="mb-3 flex flex-wrap items-center gap-2">
                      <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-bold text-emerald-900">
                        Edit #{i + 1}
                      </span>
                    </div>
                    <div className="mb-3 rounded-lg border-2 border-blue-200 bg-blue-50 px-4 py-3">
                      <p className="text-xs font-semibold uppercase tracking-wide text-blue-800">
                        Resume section
                      </p>
                      <p className="mt-1 text-base font-bold text-blue-950">
                        {edit.section}
                      </p>
                      <p className="mt-1 text-sm text-blue-900">
                        {edit.sectionHint ??
                          `Find this bullet under "${edit.section}" in your uploaded resume.`}
                      </p>
                      {edit.matchedKeywords && edit.matchedKeywords.length > 0 && (
                        <p className="mt-2 text-xs text-blue-800">
                          Already in this bullet:{" "}
                          <span className="font-medium">
                            {edit.matchedKeywords.join(", ")}
                          </span>
                        </p>
                      )}
                      {edit.targetMissingKeywords &&
                        edit.targetMissingKeywords.length > 0 && (
                          <p className="mt-1 text-xs text-amber-900">
                            Missing JD keywords we try to add:{" "}
                            <span className="font-medium">
                              {edit.targetMissingKeywords.join(", ")}
                            </span>
                          </p>
                        )}
                      {edit.addedKeywords && edit.addedKeywords.length > 0 && (
                        <p className="mt-1 text-xs text-emerald-900">
                          Added in rewrite:{" "}
                          <span className="font-medium">
                            {edit.addedKeywords.join(", ")}
                          </span>
                        </p>
                      )}
                    </div>
                    <div className="rounded-lg border border-red-100 bg-red-50 px-3 py-2 text-sm text-zinc-700">
                      <p className="mb-1 text-xs font-semibold text-red-700">Your current bullet (from resume):</p>
                      {edit.original}
                    </div>
                    <div className="mt-2 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm font-medium text-zinc-900">
                      <p className="mb-1 text-xs font-semibold text-emerald-700">Rewrite it as:</p>
                      {edit.suggested}
                    </div>
                    <p className="mt-2 text-xs text-zinc-500">
                      <span className="font-medium">Why:</span> {edit.reason}
                    </p>
                  </li>
                ))}
              </ol>
            </section>
          )}

          {changeSummary.length > 0 && (
            <ul className="list-inside list-disc text-sm text-zinc-700">
              {changeSummary.map((c, i) => (
                <li key={`${i}-${c}`}>{c}</li>
              ))}
            </ul>
          )}

          <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-lg font-semibold text-zinc-900">
                Editable draft (copy into Word)
              </h2>
              <button
                type="button"
                onClick={copyText}
                className="rounded-lg border border-zinc-300 px-3 py-1.5 text-sm font-medium hover:bg-zinc-50"
              >
                {copied ? "Copied!" : "Copy all"}
              </button>
            </div>
            <textarea
              value={editableText}
              onChange={(e) => setEditableText(e.target.value)}
              rows={16}
              className={`${fieldTextareaClass} mt-4 font-mono`}
            />
          </section>

          <div className="flex flex-wrap gap-3">
            <a
              href={`/api/run/jd/${result.runId}/download?format=docx`}
              download
              className="inline-flex items-center justify-center rounded-xl border border-zinc-300 px-4 py-3 text-sm font-medium text-zinc-800 hover:bg-zinc-50"
            >
              Download plain Word (.docx)
            </a>
            <a
              href={`/api/run/jd/${result.runId}/download?format=txt`}
              download
              className="inline-flex items-center justify-center rounded-xl border border-zinc-300 px-4 py-3 text-sm font-medium text-zinc-800 hover:bg-zinc-50"
            >
              Download text (.txt)
            </a>
          </div>
        </div>
      )}
    </>
  );
}
