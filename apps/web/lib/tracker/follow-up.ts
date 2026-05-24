import type { ApplicationEntry } from "@/lib/tracker/types";

export type FollowUpDraft = {
  subject: string;
  body: string;
  linkedInMessage: string;
  kind: "no_reply" | "checking_in";
  daysSinceOutreach: number;
};

export const DEFAULT_FOLLOW_UP_DAYS = 5;

export function daysSince(iso: string): number {
  const ms = Date.now() - new Date(iso).getTime();
  return Math.max(0, Math.floor(ms / (1000 * 60 * 60 * 24)));
}

/** When we count “last outreach” for follow-up timing. */
export function getOutreachSentAt(entry: ApplicationEntry): string | null {
  return entry.outreachSentAt ?? null;
}

export function followUpSuggested(
  entry: ApplicationEntry,
  thresholdDays = DEFAULT_FOLLOW_UP_DAYS,
): boolean {
  if (entry.status === "rejected" || entry.status === "offer") return false;
  if (entry.status === "replied" || entry.status === "interview") return false;

  const sent = getOutreachSentAt(entry);
  if (!sent) return false;

  return (
    (entry.status === "applied" || entry.status === "saved") &&
    daysSince(sent) >= thresholdDays
  );
}

function firstName(full: string | null): string {
  if (!full?.trim()) return "there";
  return full.trim().split(/\s+/)[0] || "there";
}

export function buildFollowUpDraft(
  entry: ApplicationEntry,
  thresholdDays = DEFAULT_FOLLOW_UP_DAYS,
): FollowUpDraft {
  const sent = getOutreachSentAt(entry) ?? entry.updatedAt;
  const days = daysSince(sent);
  const name = firstName(entry.contactName);
  const role = entry.role.trim();
  const company = entry.company.trim();

  const subject = `Following up — ${role} at ${company}`;

  const body = `Hi ${name},

I hope you are doing well. I wanted to follow up on my note regarding the ${role} opportunity at ${company}.

I remain very interested in the role and would welcome a brief conversation if you have time. I am happy to share more detail on my background or walk through how I could contribute to your team.

Thank you again for your time.

Best regards`;

  const linkedInMessage = `Hi ${name} — following up on my note about the ${role} role at ${company}. Still very interested and happy to connect briefly if convenient. Thank you.`;

  return {
    subject,
    body,
    linkedInMessage,
    kind: days >= thresholdDays ? "no_reply" : "checking_in",
    daysSinceOutreach: days,
  };
}
