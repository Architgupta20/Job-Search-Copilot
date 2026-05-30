import type { ApplicationEntry } from "@/lib/tracker/types";

export type ColdOutreachDraft = {
  subject: string;
  body: string;
  linkedInMessage: string;
  companyAngle?: string;
  warning?: string;
  source?: string;
};

export async function fetchColdOutreachDraft(input: {
  companyName: string;
  personName: string;
  personTitle: string;
  matchedRole?: string | null;
  companyDomain?: string | null;
  resumeId?: string | null;
}): Promise<ColdOutreachDraft> {
  const res = await fetch("/api/run/company/cold-email", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      companyName: input.companyName,
      companyDomain: input.companyDomain ?? null,
      personName: input.personName,
      personTitle: input.personTitle,
      matchedRole: input.matchedRole ?? null,
      resumeId: input.resumeId ?? null,
    }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.error ?? "Draft failed.");
  }
  return {
    subject: data.subject,
    body: data.body,
    linkedInMessage: data.linkedInMessage ?? "",
    companyAngle: data.companyAngle,
    warning: data.warning,
    source: data.source,
  };
}

export function buildCompanyOutreachUrl(entry: ApplicationEntry): string {
  const params = new URLSearchParams();
  params.set("mode", "outreach");
  params.set("company", entry.company);
  params.set("role", entry.role);
  if (entry.contactName) params.set("name", entry.contactName);
  if (entry.contactLinkedIn) params.set("linkedin", entry.contactLinkedIn);
  if (entry.contactEmail) params.set("email", entry.contactEmail);
  return `/company?${params.toString()}`;
}
