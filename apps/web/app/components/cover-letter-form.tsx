"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import type { CoverLetterResult } from "@/lib/cover-letter/types";
import { getResumeSession } from "@/lib/resume/session";
import {
  checkboxClass,
  fieldInputClass,
  fieldLabelClass,
  fieldTextareaClass,
} from "@/lib/ui/form-styles";

export function CoverLetterForm() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CoverLetterResult | null>(null);
  const [editableBody, setEditableBody] = useState("");
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
    const companyName = String(form.get("company") ?? "").trim();
    const roleTitle = String(form.get("role") ?? "").trim();
    const jdText = String(form.get("jd") ?? "").trim();
    const companyDomain = String(form.get("domain") ?? "").trim();
    const confirmed = form.get("confirm") === "on";

    if (!companyName || !roleTitle) {
      setError("Company name and role title are required.");
      return;
    }
    if (!confirmed) {
      setError("Please confirm your resume is accurate.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch("/api/run/cover-letter", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resumeId: session.id,
          companyName,
          roleTitle,
          jdText: jdText || null,
          companyDomain: companyDomain || null,
          confirmed: true,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Cover letter failed.");
      const typed = data as CoverLetterResult;
      setResult(typed);
      setEditableBody(typed.body ?? "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Cover letter failed.");
    } finally {
      setLoading(false);
    }
  }

  async function copyBody() {
    await navigator.clipboard.writeText(editableBody);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <>
      <div>
        <Link href="/" className="text-sm text-zinc-500 hover:text-zinc-800">
          ← Back
        </Link>
        <h1 className="mt-4 text-2xl font-semibold text-zinc-900">
          Cover letter generator
        </h1>
        <p className="mt-2 text-zinc-600">
          Drafts a cover letter from your resume only — optional JD improves keyword
          alignment. No invented experience.
        </p>
      </div>

      <form
        onSubmit={onSubmit}
        className="space-y-6 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm"
      >
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="company" className={fieldLabelClass}>
              Company name
            </label>
            <input
              id="company"
              name="company"
              required
              className={fieldInputClass}
              placeholder="Tarro"
            />
          </div>
          <div>
            <label htmlFor="role" className={fieldLabelClass}>
              Role title
            </label>
            <input
              id="role"
              name="role"
              required
              className={fieldInputClass}
              placeholder="Data Scientist"
            />
          </div>
        </div>
        <div>
          <label htmlFor="domain" className={fieldLabelClass}>
            Company domain (optional)
          </label>
          <input
            id="domain"
            name="domain"
            className={fieldInputClass}
            placeholder="tarro.com"
          />
        </div>
        <div>
          <label htmlFor="jd" className={fieldLabelClass}>
            Job description (optional, improves keyword match)
          </label>
          <textarea
            id="jd"
            name="jd"
            rows={8}
            placeholder="Paste JD to align keywords from your resume…"
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
          {loading ? "Drafting cover letter…" : "Generate cover letter"}
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

          {result.jdKeywordsMatched.length > 0 && (
            <p className="text-sm text-emerald-800">
              JD keywords from your resume used:{" "}
              <strong>{result.jdKeywordsMatched.join(", ")}</strong>
            </p>
          )}

          {result.resumeBulletsUsed.length > 0 && (
            <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
              <h2 className="text-sm font-semibold text-zinc-900">
                Resume bullets referenced
              </h2>
              <ul className="mt-2 list-inside list-disc text-sm text-zinc-700">
                {result.resumeBulletsUsed.map((b) => (
                  <li key={b}>{b}</li>
                ))}
              </ul>
            </section>
          )}

          <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-lg font-semibold text-zinc-900">
                Cover letter draft
              </h2>
              <button
                type="button"
                onClick={copyBody}
                className="rounded-lg border border-zinc-300 px-3 py-1.5 text-sm font-medium hover:bg-zinc-50"
              >
                {copied ? "Copied!" : "Copy all"}
              </button>
            </div>
            <textarea
              value={editableBody}
              onChange={(e) => setEditableBody(e.target.value)}
              rows={18}
              className={`${fieldTextareaClass} mt-4 font-mono text-sm`}
            />
          </section>
        </div>
      )}
    </>
  );
}
