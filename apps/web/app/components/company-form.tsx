"use client";

import Link from "next/link";
import { FormEvent, useRef, useState } from "react";
import type { CompanyRunResult } from "@/lib/company/types";
import { JobOpeningCard } from "@/app/components/job-opening-card";
import { PersonCard } from "@/app/components/person-card";
import { downloadCompanyResultsCsv } from "@/lib/company/export-csv";
import { PEOPLE_PER_ROLE, ROLE_GROUPS } from "@/lib/company/roles";
import { getResumeSession, useResumeSession } from "@/lib/resume/session";

export function CompanyForm() {
  const resumeSession = useResumeSession();
  const rolesRef = useRef<HTMLFieldSetElement>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CompanyRunResult | null>(null);

  function setAllRoles(checked: boolean) {
    rolesRef.current
      ?.querySelectorAll<HTMLInputElement>('input[name="roles"]')
      .forEach((el) => {
        el.checked = checked;
      });
  }

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setResult(null);

    const session = getResumeSession();
    const form = new FormData(e.currentTarget);
    const companyName = String(form.get("company") ?? "").trim();
    const roles = form.getAll("roles").map(String);

    if (!companyName) {
      setError("Enter a company name.");
      return;
    }
    if (roles.length === 0) {
      setError("Select at least one target role.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch("/api/run/company", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resumeId: session?.id ?? null,
          companyName,
          targetRoles: roles,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Search failed.");
      setResult(data as CompanyRunResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed.");
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
          Company search
        </h1>
        <p className="mt-2 text-zinc-600">
          <strong>People:</strong> up to {PEOPLE_PER_ROLE} <strong>senior</strong>{" "}
          LinkedIn profiles per role you pick — only that role or close equivalents
          (e.g. AI Engineer → ML / GenAI / Head of AI). Ranked Director / Head /
          Principal first. <strong>Jobs:</strong> careers portal is found automatically
          (company site, Greenhouse, Lever). ATS % and tailoring need a resume on home.
        </p>
      </div>

      {!resumeSession && (
        <p className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          <Link href="/" className="font-medium underline">
            Upload your resume
          </Link>{" "}
          on the home page to see ATS scores and tailor for each job.
        </p>
      )}

      <form
        onSubmit={onSubmit}
        className="space-y-6 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm"
      >
        <div>
          <label
            htmlFor="company"
            className="block text-sm font-medium text-zinc-800"
          >
            Company name
          </label>
          <input
            id="company"
            name="company"
            type="text"
            required
            placeholder="e.g. Stripe, Anthropic, Databricks"
            className="mt-2 w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 outline-none focus:ring-2 focus:ring-emerald-600"
          />
        </div>

        <fieldset ref={rolesRef}>
          <legend className="text-sm font-medium text-zinc-800">
            Job roles (optional filters)
          </legend>
          <p className="mt-1 text-xs text-zinc-500">
            Pick <strong>one or more</strong> — only 1 role is enough. Each role
            adds up to {PEOPLE_PER_ROLE} LinkedIn people (3 roles → up to 30).
          </p>
          <div className="mt-2 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setAllRoles(true)}
              className="rounded-lg border border-zinc-300 px-2 py-1 text-xs font-medium hover:bg-zinc-50"
            >
              Select all
            </button>
            <button
              type="button"
              onClick={() => setAllRoles(false)}
              className="rounded-lg border border-zinc-300 px-2 py-1 text-xs font-medium hover:bg-zinc-50"
            >
              Clear
            </button>
          </div>
          <div className="mt-3 max-h-80 space-y-4 overflow-y-auto">
            {Object.entries(ROLE_GROUPS).map(([group, roles]) => (
              <div key={group}>
                <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
                  {group}
                </p>
                <div className="mt-2 grid gap-2 sm:grid-cols-2">
                  {roles.map((role) => (
                    <label
                      key={role}
                      className="flex cursor-pointer items-center gap-2 rounded-lg border border-zinc-200 px-3 py-2 text-sm hover:bg-zinc-50"
                    >
                      <input type="checkbox" name="roles" value={role} />
                      {role}
                    </label>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </fieldset>

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-xl bg-zinc-900 px-4 py-3 text-sm font-medium text-white transition hover:bg-zinc-700 disabled:cursor-wait disabled:opacity-70"
        >
          {loading ? "Searching careers portal… (30–90s)" : "Search company"}
        </button>

        {error && (
          <p className="text-sm text-red-600" role="alert">
            {error}
          </p>
        )}
      </form>

      {result && (
        <div className="space-y-8">
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => downloadCompanyResultsCsv(result)}
              className="rounded-xl border border-zinc-300 bg-white px-4 py-2 text-sm font-medium hover:bg-zinc-50"
            >
              Download CSV
            </button>
          </div>

          {result.warnings.length > 0 && (
            <ul className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
              {result.warnings.map((w) => (
                <li key={w}>• {w}</li>
              ))}
            </ul>
          )}

          <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-zinc-900">Company</h2>
            <p className="mt-2 text-sm text-zinc-600">
              Domain: {result.company.domain ?? "—"}
            </p>
            {result.company.careersUrl && (
              <a
                href={result.company.careersUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-1 inline-block text-sm font-medium text-emerald-700 underline"
              >
                Open careers portal →
              </a>
            )}
          </section>

          <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-zinc-900">
              People ({result.people.length}) —{" "}
              {result.peoplePerRole ?? PEOPLE_PER_ROLE} per role
            </h2>
            {result.peopleByRole && Object.keys(result.peopleByRole).length > 0 ? (
              <div className="mt-4 space-y-6">
                {Object.entries(result.peopleByRole).map(([role, list]) =>
                  list.length > 0 ? (
                    <div key={role}>
                      <h3 className="text-sm font-semibold text-emerald-800">
                        {role} ({list.length})
                      </h3>
                      <ul className="mt-2 divide-y divide-zinc-100">
                        {list.map((p) => (
                          <PersonCard
                            key={`${role}-${p.linkedinUrl ?? p.name}`}
                            person={p}
                            companyName={result.company.name}
                          />
                        ))}
                      </ul>
                    </div>
                  ) : null,
                )}
              </div>
            ) : result.people.length === 0 ? (
              <p className="mt-2 text-sm text-zinc-500">No people found.</p>
            ) : (
              <ul className="mt-4 divide-y divide-zinc-100">
                {result.people.map((p) => (
                  <PersonCard
                    key={`${p.name}-${p.title}`}
                    person={p}
                    companyName={result.company.name}
                  />
                ))}
              </ul>
            )}
          </section>

          <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-zinc-900">
              Job openings ({result.jobs.length})
            </h2>
            {!result.resumeAttached && (
              <p className="mt-2 text-sm text-amber-800">
                Upload a resume to see ATS scores and tailor buttons.
              </p>
            )}
            {result.jobs.length > 0 ? (
              <ul className="mt-4 space-y-3">
                {[...result.jobs]
                  .sort(
                    (a, b) =>
                      (b.atsScorePercent ?? -1) - (a.atsScorePercent ?? -1),
                  )
                  .map((j) => (
                    <JobOpeningCard key={j.url} job={j} />
                  ))}
              </ul>
            ) : (
              <p className="mt-2 text-sm text-zinc-500">
                No matching roles on careers portal — open the link above manually.
              </p>
            )}
          </section>
        </div>
      )}
    </>
  );
}
