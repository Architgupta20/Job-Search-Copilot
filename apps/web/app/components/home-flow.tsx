"use client";

import Link from "next/link";
import { useRef, useState } from "react";

type Step = "upload" | "choose-path";

export function HomeFlow() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [step, setStep] = useState<Step>("upload");
  const [fileName, setFileName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  function handleFile(file: File | undefined) {
    if (!file) return;
    setError(null);

    const allowed = [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ];
    const ext = file.name.toLowerCase();
    const validExt = ext.endsWith(".pdf") || ext.endsWith(".docx");

    if (!allowed.includes(file.type) && !validExt) {
      setError("Please upload a PDF or DOCX resume.");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setError("File must be 10 MB or smaller.");
      return;
    }

    setFileName(file.name);
    setStep("choose-path");
  }

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-8">
      <header className="space-y-2 text-center sm:text-left">
        <p className="text-sm font-medium uppercase tracking-wide text-emerald-700">
          Local recruiter tool
        </p>
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-900">
          Job Search Copilot
        </h1>
        <p className="text-zinc-600">
          Upload your resume once, then find contacts and jobs at a company—or
          tailor your resume to a job description.
        </p>
      </header>

      {step === "upload" && (
        <section className="rounded-2xl border border-dashed border-zinc-300 bg-white p-8 shadow-sm">
          <h2 className="text-lg font-medium text-zinc-900">Step 1 — Upload resume</h2>
          <p className="mt-1 text-sm text-zinc-500">
            DOCX recommended for best download formatting. PDF also supported.
          </p>

          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            className="hidden"
            onChange={(e) => handleFile(e.target.files?.[0])}
          />

          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            className="mt-6 w-full rounded-xl bg-zinc-900 px-4 py-3 text-sm font-medium text-white transition hover:bg-zinc-700"
          >
            Choose resume file
          </button>

          {error && (
            <p className="mt-4 text-sm text-red-600" role="alert">
              {error}
            </p>
          )}
        </section>
      )}

      {step === "choose-path" && (
        <section className="space-y-6">
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
            Resume ready: <span className="font-medium">{fileName}</span>
            <button
              type="button"
              className="ml-3 underline hover:no-underline"
              onClick={() => {
                setStep("upload");
                setFileName(null);
                if (inputRef.current) inputRef.current.value = "";
              }}
            >
              Change file
            </button>
          </div>

          <h2 className="text-lg font-medium text-zinc-900">Step 2 — Choose path</h2>

          <div className="grid gap-4 sm:grid-cols-2">
            <Link
              href="/company"
              className="group rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm transition hover:border-zinc-400 hover:shadow-md"
            >
              <h3 className="font-semibold text-zinc-900 group-hover:text-emerald-800">
                Company name
              </h3>
              <p className="mt-2 text-sm text-zinc-600">
                Top people to cold email plus AI/ML/Data job openings on their
                careers portal.
              </p>
            </Link>

            <Link
              href="/jd"
              className="group rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm transition hover:border-zinc-400 hover:shadow-md"
            >
              <h3 className="font-semibold text-zinc-900 group-hover:text-emerald-800">
                Job description (JD)
              </h3>
              <p className="mt-2 text-sm text-zinc-600">
                Tailor your resume to the JD using only facts from your resume,
                then download.
              </p>
            </Link>
          </div>
        </section>
      )}
    </div>
  );
}
