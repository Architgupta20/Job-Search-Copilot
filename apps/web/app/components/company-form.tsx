"use client";

import Link from "next/link";
import { FormEvent, useEffect, useRef, useState } from "react";
import type { CompanyRunResult } from "@/lib/company/types";
import type { ServiceConfig } from "@/lib/config/types";
import { JobOpeningCard } from "@/app/components/job-opening-card";
import { ManualOutreachPanel } from "@/app/components/manual-outreach-panel";
import { PersonCard } from "@/app/components/person-card";
import { ServiceStatusBanner } from "@/app/components/service-status-banner";
import { downloadCompanyResultsCsv } from "@/lib/company/export-csv";
import { PEOPLE_PER_ROLE, ROLE_GROUPS } from "@/lib/company/roles";
import { getResumeSession, useResumeSession } from "@/lib/resume/session";
import {
  checkboxClass,
  fieldInputClass,
  fieldLabelClass,
  roleOptionClass,
} from "@/lib/ui/form-styles";

type CompanyMode = "search" | "manual";

export function CompanyForm() {
  const { session: resumeSession } = useResumeSession();
  const rolesRef = useRef<HTMLFieldSetElement>(null);
  const [mode, setMode] = useState<CompanyMode>("manual");
  const [serpapiAvailable, setSerpapiAvailable] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CompanyRunResult | null>(null);

  useEffect(() => {
    fetch("/api/config")
      .then((res) => res.json())
      .then((data: ServiceConfig) => {
        const available = data.serpapi?.available ?? false;
        setSerpapiAvailable(available);
        setMode(available ? "search" : "manual");
      })
      .catch(() => {
        setSerpapiAvailable(false);
        setMode("manual");
      });
  }, []);

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

  function tabClass(active: boolean) {
    return active
      ? "border-zinc-900 bg-zinc-900 text-white"
      : "border-zinc-300 bg-white text-zinc-800 hover:bg-zinc-50";
  }

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-semibold text-zinc-900">Company</h1>
        <p className="mt-2 text-zinc-600">
          Automated search finds LinkedIn people and careers jobs (SerpAPI). Manual
          outreach lets you add contacts yourself and still draft email + LinkedIn.
        </p>
      </div>

      <ServiceStatusBanner />

      <div
        className="flex flex-wrap gap-2"
        role="tablist"
        aria-label="Company mode"
      >
        <button
          type="button"
          role="tab"
          aria-selected={mode === "search"}
          onClick={() => setMode("search")}
          className={`rounded-lg border px-4 py-2 text-sm font-semibold ${tabClass(mode === "search")}`}
        >
          Automated search
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={mode === "manual"}
          onClick={() => setMode("manual")}
          className={`rounded-lg border px-4 py-2 text-sm font-semibold ${tabClass(mode === "manual")}`}
        >
          Manual outreach
        </button>
      </div>

      <div className="flex flex-col gap-6">
      {mode === "manual" && <ManualOutreachPanel />}

      {mode === "search" && !serpapiAvailable && (
        <p className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          Automated search is off. Add{" "}
          <code className="rounded bg-amber-100 px-1">SERPAPI_API_KEY</code> to{" "}
          <code className="rounded bg-amber-100 px-1">apps/web/.env</code>, or set{" "}
          <code className="rounded bg-amber-100 px-1">SERPAPI_DISABLED=false</code>{" "}
          when your quota resets. Use <strong>Manual outreach</strong> in the
          meantime.
        </p>
      )}

      {mode === "search" && (
        <>
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
          <label htmlFor="company" className={fieldLabelClass}>
            Company name
          </label>
          <input
            id="company"
            name="company"
            type="text"
            required
            placeholder="e.g. Stripe, Anthropic, Databricks"
            className={fieldInputClass}
          />
        </div>

        <fieldset ref={rolesRef}>
          <legend className={fieldLabelClass}>
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
                    <label key={role} className={roleOptionClass}>
                      <input
                        type="checkbox"
                        name="roles"
                        value={role}
                        className={checkboxClass}
                      />
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
          disabled={loading || !serpapiAvailable}
          className="w-full rounded-xl bg-zinc-900 px-4 py-3 text-sm font-medium text-white transition hover:bg-zinc-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading
            ? "Searching… (people + email research 30–90s)"
            : "Search company"}
        </button>

        {error && (
          <p className="text-sm text-red-600" role="alert">
            {error}
          </p>
        )}
      </form>

      {result && (
        <div className="mt-10 space-y-8">
          {result.warnings.length > 0 && (
            <ul className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
              {result.warnings.map((w) => (
                <li key={w}>• {w}</li>
              ))}
            </ul>
          )}

          <div className="pt-2">
            <button
              type="button"
              onClick={() => downloadCompanyResultsCsv(result)}
              className="rounded-xl border border-zinc-300 bg-white px-5 py-2.5 text-sm font-semibold text-zinc-900 shadow-sm hover:bg-zinc-50"
            >
              Download CSV
            </button>
          </div>

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
                      <div className="mt-4 space-y-0">
                        {list.map((p) => (
                          <PersonCard
                            key={`${role}-${p.linkedinUrl ?? p.name}`}
                            person={p}
                            companyName={result.company.name}
                            companyDomain={result.company.domain}
                          />
                        ))}
                      </div>
                    </div>
                  ) : null,
                )}
              </div>
            ) : result.people.length === 0 ? (
              <p className="mt-2 text-sm text-zinc-500">No people found.</p>
            ) : (
              <div className="mt-4 space-y-0">
                {result.people.map((p) => (
                  <PersonCard
                    key={`${p.name}-${p.title}`}
                    person={p}
                    companyName={result.company.name}
                    companyDomain={result.company.domain}
                  />
                ))}
              </div>
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
      )}
      </div>
    </div>
  );
}
