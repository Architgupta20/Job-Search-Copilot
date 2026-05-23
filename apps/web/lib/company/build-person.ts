import type { PersonResult } from "@/lib/company/types";

export function buildManualPerson(input: {
  name: string;
  title: string;
  linkedinUrl?: string;
  email?: string;
  matchedRole?: string;
}): PersonResult {
  const email = input.email?.trim() || null;
  return {
    name: input.name.trim(),
    title: input.title.trim(),
    linkedinUrl: input.linkedinUrl?.trim() || null,
    email,
    phone: null,
    emailConfidence: email ? "likely" : "not_found",
    phoneConfidence: "not_found",
    source: "manual",
    matchedRole: input.matchedRole?.trim() || undefined,
  };
}
