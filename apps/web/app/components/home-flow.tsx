"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import {
  clearResumeSession,
  getResumeSession,
  saveResumeSession,
} from "@/lib/resume/session";

type Step = "upload" | "choose-path";

type UploadResult = {
  id: string;
  fileName: string;
  claimCount: number;
  contact: { name?: string; email?: string };
};

export function HomeFlow() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [step, setStep] = useState<Step>("upload");
  const [fileName, setFileName] = useState<string | null>(null);
  const [uploadMeta, setUploadMeta] = useState<UploadResult | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const existing = getResumeSession();
    if (existing) {
      setUploadMeta({
        id: existing.id,
        fileName: existing.fileName,
        claimCount: 0,
        contact: {},
      });
      setFileName(existing.fileName);
      setStep("choose-path");
    }
  }, []);

  async function handleFile(file: File | undefined) {
    if (!file) return;
    setError(null);

    const ext = file.name.toLowerCase();
    const validExt = ext.endsWith(".pdf") || ext.endsWith(".docx");

    if (!validExt) {
      setError("Please upload a PDF or DOCX resume.");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setError("File must be 10 MB or smaller.");
      return;
    }

    setUploading(true);
    setFileName(file.name);

    try {
      const body = new FormData();
      body.append("file", file);

      const res = await fetch("/api/resume/upload", {
        method: "POST",
        body,
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error ?? "Upload failed.");
      }

      saveResumeSession(data.id, data.fileName);
      setUploadMeta({
        id: data.id,
        fileName: data.fileName,
        claimCount: data.claimCount,
        contact: data.contact ?? {},
      });
      setStep("choose-path");
    } catch (e) {
      setFileName(null);
      setError(e instanceof Error ? e.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  }

  function resetUpload() {
    clearResumeSession();
    setStep("upload");
    setFileName(null);
    setUploadMeta(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
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
          <h2 className="text-lg font-medium text-zinc-900">
            Step 1 — Upload resume
          </h2>
          <p className="mt-1 text-sm text-zinc-500">
            DOCX recommended for best download formatting. PDF also supported.
          </p>

          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.docx"
            className="hidden"
            disabled={uploading}
            onChange={(e) => handleFile(e.target.files?.[0])}
          />

          <button
            type="button"
            disabled={uploading}
            onClick={() => inputRef.current?.click()}
            className="mt-6 w-full rounded-xl bg-zinc-900 px-4 py-3 text-sm font-medium text-white transition hover:bg-zinc-700 disabled:cursor-wait disabled:opacity-70"
          >
            {uploading ? "Uploading & parsing…" : "Choose resume file"}
          </button>

          {error && (
            <p className="mt-4 text-sm text-red-600" role="alert">
              {error}
            </p>
          )}
        </section>
      )}

      {step === "choose-path" && uploadMeta && (
        <section className="space-y-6">
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
            <p>
              Saved: <span className="font-medium">{uploadMeta.fileName}</span>
            </p>
            {uploadMeta.claimCount > 0 && (
              <p className="mt-1 text-emerald-800">
                Parsed {uploadMeta.claimCount} factual lines for tailoring
                (nothing invented).
              </p>
            )}
            <button
              type="button"
              className="mt-2 underline hover:no-underline"
              onClick={resetUpload}
            >
              Change file
            </button>
          </div>

          <h2 className="text-lg font-medium text-zinc-900">
            Step 2 — Choose path
          </h2>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <Link
              href="/company"
              className="group rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm transition hover:border-zinc-400 hover:shadow-md"
            >
              <h3 className="font-semibold text-zinc-900 group-hover:text-emerald-800">
                Company name
              </h3>
              <p className="mt-2 text-sm text-zinc-600">
                Find people and jobs (needs SerpAPI), or use manual outreach
                when search quota is out.
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

            <Link
              href="/tracker"
              className="group rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm transition hover:border-zinc-400 hover:shadow-md sm:col-span-2 lg:col-span-1"
            >
              <h3 className="font-semibold text-zinc-900 group-hover:text-emerald-800">
                Application tracker
              </h3>
              <p className="mt-2 text-sm text-zinc-600">
                Track companies, roles, contacts, and status — saved on this
                device.
              </p>
            </Link>
          </div>
        </section>
      )}
    </div>
  );
}
