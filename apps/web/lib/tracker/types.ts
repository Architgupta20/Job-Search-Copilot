export const APPLICATION_STATUSES = [
  "saved",
  "applied",
  "replied",
  "interview",
  "offer",
  "rejected",
] as const;

export type ApplicationStatus = (typeof APPLICATION_STATUSES)[number];

export type ApplicationEntry = {
  id: string;
  company: string;
  role: string;
  contactName: string | null;
  contactLinkedIn: string | null;
  contactEmail: string | null;
  status: ApplicationStatus;
  notes: string;
  createdAt: string;
  updatedAt: string;
};

export type ApplicationInput = {
  company: string;
  role: string;
  contactName?: string | null;
  contactLinkedIn?: string | null;
  contactEmail?: string | null;
  status?: ApplicationStatus;
  notes?: string;
};

export const STATUS_LABELS: Record<ApplicationStatus, string> = {
  saved: "Saved",
  applied: "Applied",
  replied: "Replied",
  interview: "Interview",
  offer: "Offer",
  rejected: "Rejected",
};
