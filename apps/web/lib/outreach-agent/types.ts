import type { ApplicationEntry } from "@/lib/tracker/types";

export type OutreachAction =
  | "initial_outreach"
  | "follow_up"
  | "thank_reply"
  | "interview_prep"
  | "wait"
  | "none";

export type OutreachDraft = {
  subject?: string;
  body: string;
  linkedInMessage?: string;
  companyAngle?: string;
  kind?: string;
  daysSinceOutreach?: number;
};

export type OutreachPlanItem = {
  applicationId: string;
  companyName: string;
  roleTitle: string;
  status: string;
  recommendedAction: OutreachAction;
  actionLabel: string;
  priority: "high" | "medium" | "low";
  reason: string;
  draft: OutreachDraft | null;
  links: { interviewPrep?: string };
};

export type OutreachAgentResult = {
  runId: string;
  resumeId: string;
  candidateName: string;
  plans: OutreachPlanItem[];
  summary: {
    total: number;
    highPriority: number;
    byAction: Record<string, number>;
  };
  warnings: string[];
};

export function trackerToAgentPayload(entries: ApplicationEntry[]) {
  return entries.map((e) => ({
    id: e.id,
    company: e.company,
    role: e.role,
    status: e.status,
    contactName: e.contactName,
    contactTitle: e.role,
    contactEmail: e.contactEmail,
    contactLinkedIn: e.contactLinkedIn,
    outreachSentAt: e.outreachSentAt,
    notes: e.notes,
  }));
}
