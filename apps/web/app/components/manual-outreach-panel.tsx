"use client";

import { FormEvent, useState } from "react";
import type { CompanyRunResult, PersonResult } from "@/lib/company/types";
import { buildManualPerson } from "@/lib/company/build-person";
import { PersonCard } from "@/app/components/person-card";
import { downloadCompanyResultsCsv } from "@/lib/company/export-csv";
import { useResumeSession } from "@/lib/resume/session";
import { fieldInputClass, fieldLabelSmClass } from "@/lib/ui/form-styles";
import { addApplicationFromContact } from "@/lib/tracker/storage";

export function ManualOutreachPanel() {
  const { session: resumeSession } = useResumeSession();
  const [companyName, setCompanyName] = useState("");
  const [companyDomain, setCompanyDomain] = useState("");
  const [people, setPeople] = useState<PersonResult[]>([]);
  const [formError, setFormError] = useState<string | null>(null);
  const [trackerNotice, setTrackerNotice] = useState<string | null>(null);

  function onAddPerson(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setFormError(null);
    const form = new FormData(e.currentTarget);
    const name = String(form.get("name") ?? "").trim();
    const title = String(form.get("title") ?? "").trim();
    const linkedinUrl = String(form.get("linkedin") ?? "").trim();
    const email = String(form.get("email") ?? "").trim();
    const matchedRole = String(form.get("role") ?? "").trim();

    if (!companyName.trim()) {
      setFormError("Enter the company name above first.");
      return;
    }
    if (!name || !title) {
      setFormError("Name and job title are required.");
      return;
    }

    const person = buildManualPerson({
      name,
      title,
      linkedinUrl: linkedinUrl || undefined,
      email: email || undefined,
      matchedRole: matchedRole || undefined,
    });

    const { duplicate } = addApplicationFromContact({
      company: companyName.trim(),
      role: matchedRole || title,
      contactName: name,
      contactLinkedIn: linkedinUrl || null,
      contactEmail: email || null,
      status: "saved",
    });

    setTrackerNotice(
      duplicate
        ? "Already in Application tracker — contact added here for drafts."
        : "Added to Application tracker (status: Saved). Open Tracker to log email sent or draft follow-up.",
    );
    window.setTimeout(() => setTrackerNotice(null), 6000);

    setPeople((prev) => [...prev, person]);
    e.currentTarget.reset();
  }

  function removePerson(index: number) {
    setPeople((prev) => prev.filter((_, i) => i !== index));
  }

  function downloadCsv() {
    if (!companyName.trim() || people.length === 0) return;
    const result: CompanyRunResult = {
      runId: "manual",
      company: {
        name: companyName.trim(),
        domain: companyDomain.trim() || null,
        careersUrl: null,
      },
      people,
      jobs: [],
      warnings: [],
      resumeAttached: Boolean(resumeSession),
    };
    downloadCompanyResultsCsv(result);
  }

  return (
    <div className="space-y-6">
      <p className="text-sm text-zinc-600">
        Add people you found on LinkedIn yourself. Each contact is{" "}
        <strong>saved to Application tracker</strong> automatically. Use{" "}
        <strong>Find email</strong> (needs Hunter.io key) or draft{" "}
        <strong>cold email</strong> and <strong>LinkedIn</strong> below. Upload a
        resume on home for richer copy.
      </p>

      <div className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
        <h2 className="text-sm font-semibold text-zinc-900">Target company</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="manual-company" className={fieldLabelSmClass}>
              Company name
            </label>
            <input
              id="manual-company"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="e.g. Razorpay"
              className={fieldInputClass}
            />
          </div>
          <div>
            <label htmlFor="manual-domain" className={fieldLabelSmClass}>
              Company domain (optional)
            </label>
            <input
              id="manual-domain"
              value={companyDomain}
              onChange={(e) => setCompanyDomain(e.target.value)}
              placeholder="e.g. razorpay.com"
              className={fieldInputClass}
            />
          </div>
        </div>
      </div>

      <form
        onSubmit={onAddPerson}
        className="rounded-2xl border border-emerald-200 bg-white p-6 shadow-sm"
      >
        <h2 className="text-sm font-semibold text-zinc-900">Add a contact</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <div>
            <label className={fieldLabelSmClass}>Full name</label>
            <input
              name="name"
              required
              placeholder="Jane Doe"
              className={fieldInputClass}
            />
          </div>
          <div>
            <label className={fieldLabelSmClass}>
              Job title (from LinkedIn)
            </label>
            <input
              name="title"
              required
              placeholder="Director of Engineering"
              className={fieldInputClass}
            />
          </div>
          <div>
            <label className={fieldLabelSmClass}>
              Role you are targeting (optional)
            </label>
            <input
              name="role"
              placeholder="e.g. AI Engineer"
              className={fieldInputClass}
            />
          </div>
          <div>
            <label className={fieldLabelSmClass}>
              LinkedIn profile URL (optional)
            </label>
            <input
              name="linkedin"
              type="url"
              placeholder="https://linkedin.com/in/..."
              className={fieldInputClass}
            />
          </div>
          <div className="sm:col-span-2">
            <label className={fieldLabelSmClass}>
              Email (optional — if you already have it)
            </label>
            <input
              name="email"
              type="email"
              placeholder="name@company.com"
              className={fieldInputClass}
            />
          </div>
        </div>
        {formError && (
          <p className="mt-3 text-sm text-red-600" role="alert">
            {formError}
          </p>
        )}
        {trackerNotice && (
          <p className="mt-3 text-sm font-medium text-emerald-800" role="status">
            {trackerNotice}
          </p>
        )}
        <button
          type="submit"
          className="mt-4 rounded-xl bg-emerald-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-800"
        >
          Add contact + tracker
        </button>
      </form>

      {people.length > 0 && (
        <section className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-lg font-semibold text-zinc-900">
              Contacts ({people.length})
            </h2>
            <button
              type="button"
              onClick={downloadCsv}
              className="rounded-xl border border-zinc-300 bg-white px-4 py-2 text-sm font-semibold text-zinc-900 hover:bg-zinc-50"
            >
              Download CSV
            </button>
          </div>
          <div className="space-y-3">
            {people.map((p, i) => (
              <div key={`${p.name}-${i}`} className="relative">
                <button
                  type="button"
                  onClick={() => removePerson(i)}
                  className="absolute right-3 top-3 z-10 rounded border border-zinc-200 bg-white px-2 py-0.5 text-xs text-zinc-600 hover:bg-zinc-50"
                >
                  Remove
                </button>
                <PersonCard
                  person={p}
                  companyName={companyName.trim()}
                  companyDomain={companyDomain.trim() || null}
                  showSaveToTracker={false}
                />
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
