"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import type { CompanyRunResult } from "@/lib/company/types";
import { PEOPLE_PER_ROLE, TARGET_ROLES } from "@/lib/company/roles";
import { getResumeSession } from "@/lib/resume/session";

function ConfidenceBadge({ value }: { value: string }) {
  const styles: Record<string, string> = {
    verified: "bg-emerald-100 text-emerald-800",
    likely: "bg-amber-100 text-amber-900",
    not_found: "bg-zinc-100 text-zinc-600",
  };
  return (
    <span
      className={`rounded px-1.5 py-0.5 text-xs font-medium ${styles[value] ?? styles.not_found}`}
    >
      {value.replace("_", " ")}
    </span>
  );
}

export function CompanyForm() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CompanyRunResult | null>(null);

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
          resumeId: session.id,
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
          <strong>People:</strong> up to {PEOPLE_PER_ROLE} LinkedIn profiles{" "}
          <em>per role</em> you select. <strong>Jobs:</strong> deep scan of the
          careers portal (Greenhouse, Lever, ATS pages).
        </p>
      </div>

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

        <fieldset>
          <legend className="text-sm font-medium text-zinc-800">
            Job roles ({TARGET_ROLES.length} profiles — select all that apply)
          </legend>
          <p className="mt-1 text-xs text-zinc-500">
            2 roles selected → up to {PEOPLE_PER_ROLE * 2} people
          </p>
          <div className="mt-3 grid max-h-64 gap-2 overflow-y-auto sm:grid-cols-2">
            {TARGET_ROLES.map((role) => (
              <label
                key={role}
                className="flex cursor-pointer items-center gap-2 rounded-lg border border-zinc-200 px-3 py-2 text-sm hover:bg-zinc-50"
              >
                <input type="checkbox" name="roles" value={role} />
                {role}
              </label>
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
                          <li
                            key={`${role}-${p.linkedinUrl ?? p.name}`}
                            className="py-3"
                          >
                            <p className="font-medium text-zinc-900">{p.name}</p>
                            <p className="text-sm text-zinc-600">{p.title}</p>
                            {p.linkedinUrl && (
                              <a
                                href={p.linkedinUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="mt-1 inline-block text-sm text-emerald-700 underline"
                              >
                                LinkedIn
                              </a>
                            )}
                          </li>
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
                  <li key={`${p.name}-${p.title}`} className="py-4 first:pt-0">
                    <p className="font-medium text-zinc-900">
                      {p.name}
                      {p.matchedRole && (
                        <span className="ml-2 text-xs font-normal text-emerald-700">
                          ({p.matchedRole})
                        </span>
                      )}
                    </p>
                    <p className="text-sm text-zinc-600">{p.title}</p>
                    {p.linkedinUrl && (
                      <a
                        href={p.linkedinUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-2 inline-block text-sm text-emerald-700 underline"
                      >
                        LinkedIn
                      </a>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-zinc-900">
              Job openings ({result.jobs.length})
            </h2>
            {result.jobsByRole && (
              <div className="mt-4 space-y-4">
                {Object.entries(result.jobsByRole).map(([role, list]) =>
                  list.length > 0 ? (
                    <div key={role}>
                      <h3 className="text-sm font-semibold text-zinc-800">
                        {role} ({list.length})
                      </h3>
                      <ul className="mt-2 space-y-2">
                        {list.map((j) => (
                          <li
                            key={j.url}
                            className="rounded-lg border border-zinc-100 px-3 py-2"
                          >
                            <a
                              href={j.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="font-medium text-emerald-800 underline"
                            >
                              {j.title}
                            </a>
                            {j.snippet && (
                              <p className="mt-1 text-xs text-zinc-500 line-clamp-2">
                                {j.snippet}
                              </p>
                            )}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : null,
                )}
              </div>
            )}
            {result.jobs.length === 0 && (
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
