import type { AtsBreakdown, JDTailorResult } from "@/lib/jd/types";

export type ContactConfidence = "verified" | "likely" | "not_found";

export type ContactCandidate = {
  email?: string | null;
  phone?: string | null;
  source: string;
  confidence: ContactConfidence;
  score?: number;
  detail?: string;
};

export type ContactResearch = {
  sourcesChecked: string[];
  candidates: ContactCandidate[];
};

export type CompanyInfo = {
  name: string;
  domain: string | null;
  careersUrl: string | null;
};

export type PersonResult = {
  name: string;
  title: string;
  linkedinUrl: string | null;
  email: string | null;
  phone: string | null;
  emailConfidence: ContactConfidence;
  phoneConfidence: ContactConfidence;
  source: string;
  matchedRole?: string;
  contactHints?: string[];
  contactResearch?: ContactResearch;
};

export type ColdOutreachDraft = {
  subject: string;
  body: string;
  linkedInMessage: string;
  companyAngle?: string;
  warning?: string;
  source?: string;
};

export type JobResult = {
  title: string;
  url: string;
  location: string | null;
  snippet: string | null;
  matchScore: number;
  matchedRole?: string | null;
  atsScorePercent?: number | null;
  atsBreakdown?: AtsBreakdown | null;
};

export type CompanyRunResult = {
  runId: string;
  company: CompanyInfo;
  people: PersonResult[];
  peopleByRole?: Record<string, PersonResult[]>;
  jobs: JobResult[];
  jobsByRole?: Record<string, JobResult[]>;
  peoplePerRole?: number;
  resumeAttached?: boolean;
  warnings: string[];
};

export type JobTailorResult = JDTailorResult & {
  sourceJobUrl?: string;
  sourceJobTitle?: string;
};
