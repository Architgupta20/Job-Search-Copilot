"use client";

import Link from "next/link";

export function JDForm() {
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
          Paste a JD to tailor your resume. (Tailor API — Step 17.)
        </p>
      </div>

      <form className="space-y-6 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
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
            placeholder="Paste the full job description here..."
            className="mt-2 w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 outline-none focus:ring-2 focus:ring-emerald-600"
          />
        </div>

        <label className="flex items-start gap-2 text-sm text-zinc-600">
          <input type="checkbox" name="confirm" className="mt-1" />
          I confirm my resume only contains accurate information.
        </label>

        <button
          type="button"
          disabled
          className="w-full cursor-not-allowed rounded-xl bg-zinc-300 px-4 py-3 text-sm font-medium text-zinc-600"
        >
          Tailor resume (Step 17)
        </button>
      </form>
    </>
  );
}
