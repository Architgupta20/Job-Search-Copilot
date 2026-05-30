"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import type { InterviewPrepResult } from "@/lib/interview-prep/types";
import { getResumeSession } from "@/lib/resume/session";
import {
  checkboxClass,
  fieldInputClass,
  fieldLabelClass,
  fieldTextareaClass,
} from "@/lib/ui/form-styles";

const CATEGORY_LABELS: Record<string, string> = {
  behavioral: "Behavioral",
  technical: "Technical",
  "role-fit": "Role fit",
};

const CATEGORY_STYLES: Record<string, string> = {
  behavioral: "bg-violet-100 text-violet-900",
  technical: "bg-sky-100 text-sky-900",
  "role-fit": "bg-emerald-100 text-emerald-900",
};

export function InterviewPrepForm() {
  const searchParams = useSearchParams();
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<InterviewPrepResult | null>(null);
  const [copiedId, setCopiedId] = useState<number | null>(null);

  useEffect(() => {
    const c = searchParams.get("company");
    const r = searchParams.get("role");
    if (c) setCompany(c);
    if (r) setRole(r);
  }, [searchParams]);

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
      const res = await fetch("/api/run/interview-prep", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resumeId: session.id,
          companyName,
          roleTitle,
          jdText: jdText || null,
          confirmed: true,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Interview prep failed.");
      setResult(data as InterviewPrepResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Interview prep failed.");
    } finally {
      setLoading(false);
    }
  }

  async function copyQuestion(q: InterviewPrepResult["questions"][0]) {
    const text = [
      q.question,
      "",
      "Resume anchor:",
      q.resumeAnchor,
      "",
      "STAR outline:",
      `Situation: ${q.starPrompt.situation}`,
      `Task: ${q.starPrompt.task}`,
      `Action: ${q.starPrompt.action}`,
      `Result: ${q.starPrompt.result}`,
      `Tip: ${q.starPrompt.tip}`,
    ].join("\n");
    await navigator.clipboard.writeText(text);
    setCopiedId(q.id);
    setTimeout(() => setCopiedId(null), 2000);
  }

  return (
    <>
      <div>
        <Link href="/" className="text-sm text-zinc-500 hover:text-zinc-800">
          ← Back
        </Link>
        <h1 className="mt-4 text-2xl font-semibold text-zinc-900">
          Interview prep
        </h1>
        <p className="mt-2 text-zinc-600">
          Five tailored questions with STAR prompts anchored to your resume —
          optional JD sharpens technical questions. No invented experience.
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
              value={company}
              onChange={(e) => setCompany(e.target.value)}
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
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className={fieldInputClass}
              placeholder="Data Scientist"
            />
          </div>
        </div>
        <div>
          <label htmlFor="jd" className={fieldLabelClass}>
            Job description (optional)
          </label>
          <textarea
            id="jd"
            name="jd"
            rows={8}
            placeholder="Paste JD to tailor technical questions to keywords in your resume…"
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
          {loading ? "Building prep sheet…" : "Generate interview prep"}
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

          <p className="text-sm text-zinc-600">
            {result.companyName} — {result.roleTitle}
            {result.jdKeywordsUsed.length > 0 && (
              <>
                {" "}
                · JD keywords:{" "}
                <span className="font-medium text-zinc-800">
                  {result.jdKeywordsUsed.slice(0, 8).join(", ")}
                </span>
              </>
            )}
          </p>

          <div className="space-y-4">
            {result.questions.map((q) => (
              <section
                key={q.id}
                className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="space-y-2">
                    <span
                      className={`inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${CATEGORY_STYLES[q.category] ?? "bg-zinc-100 text-zinc-800"}`}
                    >
                      {CATEGORY_LABELS[q.category] ?? q.category}
                    </span>
                    <h2 className="text-lg font-semibold text-zinc-900">
                      Q{q.id}. {q.question}
                    </h2>
                  </div>
                  <button
                    type="button"
                    onClick={() => copyQuestion(q)}
                    className="shrink-0 rounded-lg border border-zinc-300 px-3 py-1.5 text-sm font-medium hover:bg-zinc-50"
                  >
                    {copiedId === q.id ? "Copied!" : "Copy"}
                  </button>
                </div>

                <div className="mt-4 rounded-lg bg-zinc-50 px-4 py-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
                    Resume anchor
                  </p>
                  <p className="mt-1 text-sm text-zinc-800">{q.resumeAnchor}</p>
                </div>

                <dl className="mt-4 space-y-3 text-sm">
                  {(
                    [
                      ["Situation", q.starPrompt.situation],
                      ["Task", q.starPrompt.task],
                      ["Action", q.starPrompt.action],
                      ["Result", q.starPrompt.result],
                      ["Tip", q.starPrompt.tip],
                    ] as const
                  ).map(([label, text]) => (
                    <div key={label}>
                      <dt className="font-semibold text-zinc-900">{label}</dt>
                      <dd className="mt-0.5 text-zinc-700">{text}</dd>
                    </div>
                  ))}
                </dl>
              </section>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
