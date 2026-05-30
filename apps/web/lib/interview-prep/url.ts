import type { ApplicationEntry } from "@/lib/tracker/types";

export function buildInterviewPrepUrl(entry: ApplicationEntry): string {
  const params = new URLSearchParams();
  params.set("company", entry.company);
  params.set("role", entry.role);
  return `/interview-prep?${params.toString()}`;
}
