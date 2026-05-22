"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import type { JDTailorResult } from "@/lib/jd/types";
import { getResumeSession } from "@/lib/resume/session";

export function JDForm() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<JDTailorResult | null>(null);

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
      if (!res.ok) throw new Error(data.error ?? "Tailoring failed.");
      setResult(data as JDTailorResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Tailoring failed.");
    } finally {
      setLoading(false);
    }
  }

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
          Rewords your resume using JD keywords only when they match facts you
          already have — nothing invented.
        </p>
      </div>

      <form
        onSubmit={onSubmit}
        className="space-y-6 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm"
      >
        <div>
          <label
            htmlFor="jd"
            className="block text-sm font-medium text-zinc-800"
          >
            Job description
          </label>
          <textarea
            id="jd"
            name="jd"
            rows={12}
            required
            placeholder="Paste the full job description here..."
            className="mt-2 w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 outline-none focus:ring-2 focus:ring-emerald-600"
          />
        </div>

        <label className="flex items-start gap-2 text-sm text-zinc-600">
          <input type="checkbox" name="confirm" required className="mt-1" />
          I confirm my resume only contains accurate information.
        </label>

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-xl bg-zinc-900 px-4 py-3 text-sm font-medium text-white transition hover:bg-zinc-700 disabled:cursor-wait disabled:opacity-70"
        >
          {loading ? "Tailoring… (20–60s)" : "Tailor resume"}
        </button>

        {error && (
          <p className="text-sm text-red-600" role="alert">
            {error}
          </p>
        )}
      </form>

      {result && (
        <div className="space-y-6">
          {result.warnings.map((w) => (
            <p
              key={w}
              className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900"
            >
              {w}
            </p>
          ))}

          <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <h2 className="text-lg font-semibold text-zinc-900">Results</h2>
              <span className="rounded-full bg-emerald-100 px-3 py-1 text-sm font-medium text-emerald-900">
                ATS match (supported keywords): {result.atsScorePercent}%
              </span>
            </div>

            {result.jdTitle && (
              <p className="mt-2 text-sm text-zinc-600">
                Role: {result.jdTitle}
              </p>
            )}

            {result.changeSummary.length > 0 && (
              <ul className="mt-4 list-inside list-disc text-sm text-zinc-700">
                {result.changeSummary.map((c) => (
                  <li key={c}>{c}</li>
                ))}
              </ul>
            )}

            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <div>
                <h3 className="text-sm font-medium text-zinc-800">
                  Keywords used
                </h3>
                <p className="mt-1 text-sm text-zinc-600">
                  {result.keywordsUsed.length > 0
                    ? result.keywordsUsed.join(", ")
                    : "—"}
                </p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-zinc-800">
                  Not added (unsupported)
                </h3>
                <p className="mt-1 text-sm text-zinc-600">
                  {result.keywordsSkipped.length > 0
                    ? result.keywordsSkipped.join(", ")
                    : "—"}
                </p>
              </div>
            </div>

            <div className="mt-6 flex flex-wrap gap-3">
              <a
                href={`/api/run/jd/${result.runId}/download?format=docx`}
                download
                className="inline-flex items-center justify-center rounded-xl bg-emerald-700 px-4 py-3 text-sm font-medium text-white hover:bg-emerald-800"
              >
                Download Word (.docx)
              </a>
              <a
                href={`/api/run/jd/${result.runId}/download?format=txt`}
                download
                className="inline-flex items-center justify-center rounded-xl border border-zinc-300 px-4 py-3 text-sm font-medium text-zinc-800 hover:bg-zinc-50"
              >
                Download text (.txt)
              </a>
            </div>
            <p className="mt-2 text-xs text-zinc-500">
              For best formatting, upload your resume as <strong>DOCX</strong>{" "}
              (not PDF). Word download keeps your fonts and spacing.
            </p>
          </section>

          <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-zinc-900">Preview</h2>
            <pre className="mt-4 max-h-96 overflow-auto whitespace-pre-wrap rounded-lg bg-zinc-50 p-4 text-sm text-zinc-800">
              {result.tailoredText}
            </pre>
          </section>
        </div>
      )}
    </>
  );
}
